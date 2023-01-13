import math
from Acquisition import aq_parent

from Products.PluggableAuthService.interfaces.authservice import IBasicUser
from Products.PluggableAuthService.interfaces.events import ICredentialsUpdatedEvent
from ipaddress import ip_address, ip_network
from plone.registry.interfaces import IRegistry
from zope.component import getUtility, ComponentLookupError, adapter
from zope.component.hooks import getSite
from Products.LoginLockout.interfaces import ILoginLockoutSettings
try:
    from AuthEncoding import AuthEncoding
except ImportError:
    from AccessControl import AuthEncoding
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from BTrees.OOBTree import OOBTree
from DateTime import DateTime
from OFS.Cache import Cacheable
from OFS.Folder import Folder
from Products.CMFCore.utils import getToolByName
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.interfaces.plugins import IAnonymousUserFactoryPlugin  # NOQA
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin  # NOQA
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin  # NOQA
from Products.PluggableAuthService.interfaces.plugins import ICredentialsUpdatePlugin  # NOQA
from Products.PluggableAuthService.permissions import ManageUsers
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.statusmessages.interfaces import IStatusMessage
import logging
import os
import six
from zope.i18nmessageid import MessageFactory

_ = PloneMessageFactory = MessageFactory('LoginLockout')


__author__ = "Dylan Jay <software@pretaweb.com>"


"""LoginLockout.
   Locks out the user when they make too many different unsuccessful login
   attempts.

   An AuthenticateUser plugin increments a count for each login with a
   different password.

   A UpdateCredentials plugin resets that count as this indicates a successful
   login.

   If the count reaches the max then AuthenticateUser Plugin will blank out
   the credentials.
   *Important* This relies on the credentials being changed as a side effect.
   Future implementations of PAS might not allow this.
   This prevents login and a status message is shown.

   Note: Unfortunately Plone decides to also show a message that the login was incorrect
   which might be confusing


   A previous version of the plugin used another method.
   AuthenticationPlugin would throw an unauthorised exception resulting in a challenge plugin
   which would then redirect to another page. Our plugin had to be the first challenge plugin for
   this to work.

   The admin can view and reset attempts via the ZMI at any time. Password resets also reset the
   attempts.
"""

ENV_WHITELIST = 'LOGINLOCKOUT_IP_WHITELIST'


log = logging.getLogger('LoginLockout')

manage_addLoginLockoutForm = PageTemplateFile(
    'www/loginLockoutAdd',
    globals(),
    __name__='manage_addLoginLockoutForm')


def manage_addLoginLockout(dispatcher,
                           id,
                           title=None,
                           REQUEST=None):
    """Add a LoginLockout plugin to a Pluggable Auth Service."""

    obj = LoginLockout(id, title)
    dispatcher._setObject(obj.getId(), obj)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace?manage_tabs_message='
                                     'LoginLockout+plugin+added.'
                                     % dispatcher.absolute_url())


class LoginLockout(Folder, BasePlugin, Cacheable):

    """PAS plugin that rejects logins after X attemps
    """

    lockout_path = ''
    meta_type = 'Login Lockout Plugin'
    cookie_name = '__noduplicate'
    security = ClassSecurityInfo()

    _properties = (
        {'id': 'title',
         'label': 'Title',
         'type': 'string',
         'mode': 'w',
         },
        {'id': '_max_attempts',
         'label': 'Number of Allowed Attempts',
         'type': 'int',
         'mode': 'w',
         },
        {'id': '_reset_period',
         'label': 'Attempt Reset Period (hours)',
         'type': 'float',
         'mode': 'w',
         },
        {'id': '_whitelist_ips',
         'label': 'Restrict to IP ranges (127.0.0.1 always allowed)',
         'type': 'lines',
         'mode': 'w'
         },
        {'id': '_fake_client_ip',
         'label': 'Ignore HTTP_X_FORWARDED_FOR',
         'type': 'boolean',
         'mode': 'w'
         },
    )

    lockout = PageTemplateFile(
        'www/lockout.pt',
        globals(),
        __name__='lockout')

    def __init__(self, id, title=None):
        self._id = self.id = id
        self.title = title
        # userid : (Count:int, DateTime, IP:string)
        self._login_attempts = OOBTree()
        # userid : (Count:int, DateTime, IP:string)
        self._successful_login_attempts = OOBTree()
        self._last_pw_change = OOBTree()  # userid : DateTime
        self._reset_period = 24.0
        self._max_attempts = 3
        self._fake_client_ip = False
        self._whitelist_ips = []

    def remote_ip(self):
        if hasattr(self, '_fake_client_ip') and self._fake_client_ip:
            return '127.0.0.1-faked'
        ip = self.REQUEST.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        if not ip:
            ip = self.REQUEST.get('REMOTE_ADDR', '')
        return ip

    security.declarePrivate('authenticateCredentials')

    def authenticateCredentials(self, credentials):
        """See IAuthenticationPlugin.

        This plugin will actually never authenticate.
        It does clear credentials if the user is locked out
        so relies on side-effect.

        o We expect the credentials to be those returned by
          ILoginPasswordExtractionPlugin.
        """
        request = self.REQUEST
        response = request['RESPONSE']
        pas_instance = self._getPAS()

        login = credentials.get('login')
        password = credentials.get('password')

        if None in (login, password, pas_instance):
            return None
        oldlogin, oldpw, top_plugin = request.get('attempted_logins', (None, None, self))
        if top_plugin != self:
            # We are a lower plugin. We need to check against top plugin lockouts
            return top_plugin.authenticateCredentials(credentials)

        messages = IStatusMessage(request)
        IP = self.remote_ip()
        if not self._isConfiguredCorrectly():
            messages.addStatusMessage(_("LoginLockout incorrectly configured"), type="error")
            return None
        elif self.isIPLocked(login, six.text_type(IP)):
            log.info("Attempt denied due to IP: %s, %s ", login, IP)
            messages.addStatusMessage(_("Login currently unavailable"), type="error")  # TODO Is this a good idea?
            credentials.clear()
        elif self.isLockedout(login):
            messages.addStatusMessage(self._lockoutMessage(login), type="error")
            request['locked_login'] = (login, self)  # so challenge plugin can fire
            # HACK - need ot reset in current request not just response like
            # cookie auth does
            request.set('__ac', '')
            # must reset so we don't lockout of the login page
            self.resetAllCredentials(request, response)
            count, last, IP = self.getAttempts(login)
            log.info("Attempt denied due to lockout: %s, %s ", login, IP)
            # TODO: ensure resetting credentials locks the user out in all cases?
            credentials.clear()

        # Used when creating anon user to setAttempt and display warning
        if not request.get('attempted_logins'):
            request.set('attempted_logins', (login, password, self))

        return None  # Note that we never return anything useful

    security.declarePrivate('createAnonymousUser')

    def createAnonymousUser(self):
        """ if we got anon then attempt failed """
        login, password, plugin = self.REQUEST.get('attempted_logins', ('', '', None))
        if not login:
            return

        left = self.getMaxAttempts() - self.setAttempt(login, password, plugin)
        log.info("Failed login attempt: %s ", login)
        messages = IStatusMessage(self.REQUEST)
        if left > 0:
            msgid = _(
                u"lockout_attempt_warning",
                default=u"You have ${attempts_left} attempts left before this account is locked",
                mapping={u"attempts_left": left}
            )
            messages.addStatusMessage(msgid, type="warning")
        elif left == 0:
            messages.addStatusMessage(self._lockoutMessage(login, plugin), type="error")

    security.declarePrivate('updateCredentials')

    def updateCredentials(self, request, response, login, new_password):

        """ Called on succesful attempt. reset user
        """
        self.resetAttempts(login, new_password)
        log.info("Successful login: %s ", login)

    security.declarePrivate('_lockoutMessage')

    def _lockoutMessage(self, login, plugin=None):
        plugin = self if plugin is None else plugin

        count, last, IP, pw_hash = plugin._login_attempts.get(
            login, (0, None, '', ''))

        reset_period = int(math.ceil(self.getResetPeriod() - ((DateTime() - last) * 24)))
        msgid = _(
            u"description_login_locked",
            default=u"This account has now been locked for security purposes. Try again after ${reset_period} hours or reset your password below",
            mapping={u"reset_period": reset_period}
        )
        # translated = self.translate(msgid)
        return msgid

    def _isConfiguredCorrectly(self):
        plugins = self.aq_parent.plugins.listPlugins(IAuthenticationPlugin)
        return self == plugins[0][1]

    security.declarePrivate('setAttempt')

    def setAttempt(self, login, password, plugin):
        "increment attempt count and record date stamp last attempt and IP"

        count, last, IP, reference = plugin._login_attempts.get(
            login, (0, None, '', None))

        IP = self.remote_ip()
        if reference and AuthEncoding.pw_validate(reference, password):
            # we don't count repeating same password in case its correct
            return count
        if last and ((DateTime() - last) * 24) > self.getResetPeriod():
            # set count to 1 following login attempt after reset period
            count = 1
        elif count >= self.getMaxAttempts() or self.isIPLocked(login, IP):
            # Don't keep recording after its already locked
            return count
        else:
            count += 1
        log.info("user '%s' attempt #%i %s last: %s", login, count, IP, last)
        last = DateTime()
        reference = AuthEncoding.pw_encrypt(password)
        plugin._login_attempts[login] = (count, last, IP, reference)
        return count

    security.declarePrivate('setSuccessfulAttempt')

    def setSuccessfulAttempt(self, login):
        "increment attempt count and record date stamp last attempt and IP"
        # root = self.getRootPlugin()
        last = DateTime()
        assert hasattr(self, "_successful_login_attempts")
        if login not in self._successful_login_attempts:
            self._successful_login_attempts[login] = list()
        old = self._successful_login_attempts[login]
        old.append(dict(last=last, ip=self.remote_ip()))
        self._successful_login_attempts[login] = old

    security.declarePrivate('getAttempts')

    def getAttempts(self, login):
        "return the count, last attempt datestamp and IP of last attempt"
        # root = self.getRootPlugin()
        assert hasattr(self, "_login_attempts")
        count, last, IP, pw_hash = self._login_attempts.get(
            login, (0, None, '', ''))
        if last and ((DateTime() - last) * 24) > self.getResetPeriod():
            count = 1
        return count, last, IP

    def _getsetting(self, setting):

        default = getattr(self, '_' + setting)

        try:
            # Ensure we get locally from the plone site and not some other plone site
            registry = getUtility(IRegistry, context=aq_parent(aq_parent(self)))
            settings = registry.forInterface(ILoginLockoutSettings, prefix="Products.LoginLockout")
            return getattr(settings, setting)
        except ComponentLookupError:
            pass
        try:
            p_tool = getToolByName(self, 'portal_properties')
            return p_tool.loginlockout_properties.getProperty(setting, default)
        except AttributeError:
            pass
        return default

    security.declarePublic('getResetPeriod')

    def getResetPeriod(self):
        return self._getsetting('reset_period')

    security.declarePrivate('getMaxAttempts')

    def getMaxAttempts(self):
        return self._getsetting('max_attempts')

    security.declarePrivate('getWhitelistIPs')

    def getWhitelistIPs(self):
        value = self._getsetting('whitelist_ips')
        if not value:
            return []
        # remove comments
        if isinstance(value, six.string_types):
            ranges = [x.split('#')[0].strip() for x in value.split('\n')]
        else:
            ranges = list(value)
        ranges = [x for x in ranges if x]
        if not ranges:
            return []
        if ENV_WHITELIST in os.environ:
            ranges += [x.split('#')[0].strip() for x in os.environ[ENV_WHITELIST].split('\n')]

        ranges = [x for x in ranges if x]
        return ranges

    security.declarePrivate('isLockedout')

    def isLockedout(self, login):
        # root = self.getRootPlugin()
        count, last, IP = self.getAttempts(login)
        return count >= self.getMaxAttempts()

    security.declarePrivate('isIPLocked')

    def isIPLocked(self, login, ip):

        whitelist_ips = self.getWhitelistIPs()

        if not whitelist_ips:
            # Don't do the check if there is no whitelist set
            return False

        client = ip_address(six.text_type(ip))
        # TODO: could support rules that have different IP ranges for different groups
        for range in list(whitelist_ips) + ['127.0.0.1']:
            try:
                if client in ip_network(six.text_type(range)):
                    return False
            except ValueError:
                # we can get this if the range not in the right format.
                # in which case we skip this check.
                # TODO: should handle it better by validating the value when its set
                continue
        return True

    security.declarePrivate('resetAttempts')

    def resetAttempts(self, login, password=None):
        """ reset to zero and update pw reference so same attempts pass """
        # root = self.getRootPlugin()
        if self._login_attempts.get(login, None):
            del self._login_attempts[login]

    security.declarePrivate('resetAllCredentials')

    def resetAllCredentials(self, request, response, pas_instance=None):
        """Call resetCredentials of all plugins.

        o This is not part of any contract.
        """
        # This is arguably a bit hacky, but calling
        # pas_instance.resetCredentials() will not do anything because
        # the user is still anonymous.  (I think it should do
        # something nevertheless.)
        if pas_instance is None:
            pas_instance = self._getPAS()
        plugins = pas_instance._getOb('plugins')
        cred_resetters = plugins.listPlugins(ICredentialsResetPlugin)
        for resetter_id, resetter in cred_resetters:
            resetter.resetCredentials(request, response)
        # Could be authenticated at a top level so need to reset there too
        # parent = aq_parent(aq_parent(aq_inner(pas_instance)))
        # if parent is not None and parent != pas_instance:
        #     self.resetAllCredentials(request, response, parent.acl_users)

    #
    #   ZMI
    #
    manage_options = (
        (
            {'label': 'Users',
                'action': 'manage_users', },
        ) +
        BasePlugin.manage_options[:1] +
        Folder.manage_options[:1] +
        Folder.manage_options[2:]
    )

    security.declareProtected(ManageUsers, 'manage_users')
    manage_users = PageTemplateFile(
        'www/llLockouts', globals(), __name__='manage_users')

    security.declarePrivate('manage_afterAdd')

    lockout = PageTemplateFile(
        'www/lockout.pt',
        globals(),
        __name__='lockout',
    )

    security.declareProtected(ManageUsers, 'manage_resetUsers')

    def manage_resetUsers(self, logins, RESPONSE=None):
        """ Reset lockout so user can login again
        """
        for login in logins:
            self.resetAttempts(login)
        message = "User reset"
        if RESPONSE is not None:
            RESPONSE.redirect(
                '%s/manage_users?manage_tabs_message=%s' % (
                    self.absolute_url(), message)
            )

    security.declareProtected(ManageUsers, 'getAttemptInfo')

    def getAttemptInfo(self, login):
        """ user_id -> {}
        """
        count, last, IP = self.getAttempts(login)
        return {
            'login': login,
            'last': last,
            'IP': IP,
            'count': count
        }

    security.declareProtected(ManageUsers, 'listAttempts')

    def listAttempts(self):
        """ -> ( {}, ...{} )

        o Return one mapping per user, with the following keys
        """
        # root = self.getRootPlugin()
        return [self.getAttemptInfo(x) for x in self._login_attempts.keys()]

    security.declareProtected(ManageUsers, 'listSuccessfulAttempts')

    def listSuccessfulAttempts(self):

        """ -> ( {}, ...{} )

        o Return one mapping per user, with the following keys
        """
        # root = self.getRootPlugin()
        return self._successful_login_attempts

    security.declareProtected(ManageUsers, 'manage_credentialsUpdated')

    def manage_credentialsUpdated(self, username):
        """ register timestamp of last password change """
        self._last_pw_change[username] = DateTime()

    security.declareProtected(ManageUsers, 'manage_getPasswordChanges')

    def manage_getPasswordChanges(self, min_days=0):
        """ Return history of password changes where the
            timestamp is older than ``min_days`` days.
        """

        _ct = self.toLocalizedTime
        data = self._last_pw_change
        now = DateTime()
        usernames = sorted(self._last_pw_change.keys())
        return [dict(username=username, last_change=_ct(data[username]))
                for username in usernames if now - data[username] >= min_days]


classImplements(LoginLockout,
                ICredentialsUpdatePlugin,
                IAuthenticationPlugin,
                IAnonymousUserFactoryPlugin)

InitializeClass(LoginLockout)

PROJECTNAME = 'LoginLockout'
PLUGIN_ID = 'login_lockout_plugin'
PLUGIN_TITLE = 'Disable account after failed login attempts.'


def logged_in_handler(event):
    """
    Listen to loggedin event so we can reset counter
    """

    user = event.object
    portal = getSite()
    if getattr(user, 'getUserId', None) is None:
        userid = str(user)
    else:
        userid = user.getUserId()

    # TODO: don't hardcode name?
    if hasattr(portal.acl_users, 'login_lockout_plugin'):
        portal.acl_users.login_lockout_plugin.setSuccessfulAttempt(userid)


@adapter(IBasicUser, ICredentialsUpdatedEvent)
def credentials_updated_handler(principal, event):
    # TODO: currently doesn;t work because plone doesn't generate this event.
    #  https://github.com/plone/Products.PlonePAS/issues/33

    pas = aq_parent(principal)

    # portal = getSite()
    # password = event.password

    userid = principal.getId()

    # TODO: don't hardcode name?
    if hasattr(pas, 'login_lockout_plugin'):
        pas.login_lockout_plugin.manage_credentialsUpdated(userid)
