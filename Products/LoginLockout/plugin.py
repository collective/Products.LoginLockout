from ipaddress import ip_address, ip_network
from plone.registry.interfaces import IRegistry
from zope.component import getUtility, ComponentLookupError
from zope.component.hooks import getSite

from Products.LoginLockout.interfaces import ILoginLockoutSettings
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
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin  # NOQA
from Products.PluggableAuthService.interfaces.plugins import ICredentialsUpdatePlugin  # NOQA
from Products.PluggableAuthService.permissions import ManageUsers
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from zExceptions import Unauthorized
import logging
import os

__author__ = "Dylan Jay <software@pretaweb.com>"


"""LoginLockout.
   Locks out the user when they make too many different unsuccessful login
   attempts.

   An AuthenticateUser plugin increments a count for each login with a
   different password.

   A UpdateCredentials plugin resets that count as this indicates a successful
   login.

   If the count reaches the max then AuthenticateUser Plugin throws a
   Unauthorised exception.

   The challenge machinery is inacted and a Challenge plugin recognises the
   user is locked out and redirects them to a page informing them they are
   locked out and to contact the admin

   The admin can view and reset attempts via the ZMI at any time
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

    lockout_path = 'lockout'
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

        IP = self.remote_ip()
        if self.isIPLocked(login, unicode(IP)):
            # TODO: should there be some notification login is blocked due to IP?
            log.info("Attempt denied due to IP: %s, %s ", login, IP)
            raise Unauthorized

        if self.isLockedout(login):
            request['portal_status_message'] = (
                "This account is locked."
                "Please contact your administrator to unlock this account")
            request['locked_login'] = login  # so challenge plugin can fire
            # HACK - need ot reset in current request not just reponse like
            # cookie auth does
            request.set('__ac', '')
            # must reset so we don't lockout of the login page
            self.resetAllCredentials(request, response)
            count, last, IP = self.getAttempts(login)
            log.info("Attempt denied due to lockout: %s, %s ", login, IP)
            raise Unauthorized

        request.set('attempted_logins', (login, password))

        return None  # Note that we never return anything useful

    security.declarePrivate('createAnonymousUser')

    def createAnonymousUser(self):
        """ if we got anon then attempt failed """
        login, password = self.REQUEST.get('attempted_logins', ('', ''))
        if login:
            self.setAttempt(login, password)
            log.info("Failed login attempt: %s ", login)

    security.declarePrivate('updateCredentials')

    def updateCredentials(self, request, response, login, new_password):

        """ Called on succesful attempt. reset user
        """
        self.resetAttempts(login, new_password)
        log.info("Successful login: %s ", login)

    security.declarePrivate('challenge')

    def challenge(self, request, response, **kw):
        """ Challenge the user for credentials. """
        login = request.get('locked_login', None)
        if login and self.isLockedout(login):
            return self.unauthorized()
        return 0

    security.declarePrivate('unauthorized')

    def unauthorized(self):
        req = self.REQUEST
        resp = req['RESPONSE']

        # Redirect if desired.
        url = self.getLockoutURL()
        if url is not None:
            resp.redirect(url, lock=1)
            return 1

        # Could not challenge.
        return 0

    security.declarePrivate('getLockoutURL')

    def getLockoutURL(self):
        """ Where to send people for logging in """
        if self.lockout_path.startswith('/'):
            return self.lockout_path
        elif self.lockout_path != '':
            return '%s/%s' % (self.absolute_url(), self.lockout_path)
        else:
            return None

    security.declarePrivate('getRootPlugin')

    def getRootPlugin(self):
        pas = self.getPhysicalRoot().acl_users
        plugins = pas.objectValues([self.meta_type])
        if plugins:
            return plugins[0]

    security.declarePrivate('setAttempt')

    def setAttempt(self, login, password):
        "increment attempt count and record date stamp last attempt and IP"

        # TODO: why are the login attempts stored in the root? The usernames aren't unique in the root.

        root = self.getRootPlugin()
        count, last, IP, reference = root._login_attempts.get(
            login, (0, None, '', None))

        if reference and AuthEncoding.pw_validate(reference, password):
            # we don't count repeating same password in case its correct
            return
        if last and ((DateTime() - last) * 24) > self.getResetPeriod():
            # set count to 1 following login attempt after reset period
            count = 1
        else:
            count += 1
        IP = self.remote_ip()
        log.info("user '%s' attempt #%i %s last: %s", login, count, IP, last)
        last = DateTime()
        reference = AuthEncoding.pw_encrypt(password)
        root._login_attempts[login] = (count, last, IP, reference)

    security.declarePrivate('setSuccessfulAttempt')

    def setSuccessfulAttempt(self, login):
        "increment attempt count and record date stamp last attempt and IP"
        root = self.getRootPlugin()
        last = DateTime()
        if login not in root._successful_login_attempts:
            root._successful_login_attempts[login] = list()
        old = root._successful_login_attempts[login]
        old.append(dict(last=last, ip=self.remote_ip()))
        root._successful_login_attempts[login] = old

    security.declarePrivate('getAttempts')

    def getAttempts(self, login):
        "return the count, last attempt datestamp and IP of last attempt"
        root = self.getRootPlugin()
        count, last, IP, pw_hash = root._login_attempts.get(
            login, (0, None, '', ''))
        if last and ((DateTime() - last) * 24) > self.getResetPeriod():
            count = 1
        return count, last, IP

    def _getsetting(self, setting):

        default = getattr(self, '_' + setting)

        try:
            registry = getUtility(IRegistry)
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
        if isinstance(value, basestring):
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
        root = self.getRootPlugin()
        count, last, IP = root.getAttempts(login)
        return count >= root.getMaxAttempts()

    security.declarePrivate('isIPLocked')

    def isIPLocked(self, login, ip):

        whitelist_ips = self.getWhitelistIPs()

        if not whitelist_ips:
            # Don't do the check if there is no whitelist set
            return False

        client = ip_address(unicode(ip))
        # TODO: could support rules that have different IP ranges for different groups
        for range in list(whitelist_ips) + ['127.0.0.1']:
            try:
                if client in ip_network(unicode(range)):
                    return False
            except ValueError:
                # we can get this if the range not in the right format.
                # in which case we skip this check.
                # TODO: should handle it better by validating the value when its set
                continue
        return True

    security.declarePrivate('resetAttempts')

    def resetAttempts(self, login, password=None):
        """ reset to zero and update pw referece so same attempts pass """
        root = self.getRootPlugin()
        if root._login_attempts.get(login, None):
            del root._login_attempts[login]

    security.declarePrivate('resetAllCredentials')

    def resetAllCredentials(self, request, response):
        """Call resetCredentials of all plugins.

        o This is not part of any contract.
        """
        # This is arguably a bit hacky, but calling
        # pas_instance.resetCredentials() will not do anything because
        # the user is still anonymous.  (I think it should do
        # something nevertheless.)
        pas_instance = self._getPAS()
        plugins = pas_instance._getOb('plugins')
        cred_resetters = plugins.listPlugins(ICredentialsResetPlugin)
        for resetter_id, resetter in cred_resetters:
            resetter.resetCredentials(request, response)

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
        root = self.getRootPlugin()
        return [self.getAttemptInfo(x) for x in root._login_attempts.keys()]

    security.declareProtected(ManageUsers, 'listSuccessfulAttempts')

    def listSuccessfulAttempts(self):

        """ -> ( {}, ...{} )

        o Return one mapping per user, with the following keys
        """
        root = self.getRootPlugin()
        return root._successful_login_attempts

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
                IChallengePlugin,
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
