import re
from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
#from permissions import ManagePortal

from Products.CMFCore.utils import UniqueObject, getToolByName

from Products.LoginLockout.config import TOOL_ID
from Products.LoginLockout.plugin import PROJECTNAME

class LoginLockoutTool(UniqueObject,  SimpleItem):
    """ A tool to facilitate calling the plugin's methods for viewing login
    attempts, resetting attempts, etc. from a view template.
    """
    meta_type = PROJECTNAME
    id = TOOL_ID
    title = "Login Lockout Tool"
    security = ClassSecurityInfo()

    security.declarePrivate('_getPlugin')
    def _getPlugin(self):
        acl_users = getToolByName(self, 'acl_users')
        return acl_users.login_lockout_plugin

    #security.declareProtected(ManagePortal, 'listAttempts')
    def listAttempts(self):
        return self._getPlugin().listAttempts()

    def listSuccessfulAttempts(self):
        pattern = self.REQUEST.get('pattern', '')
        pattern_regex = re.compile(pattern, re.I)
        result = list()
        for username, attempts in self._getPlugin().listSuccessfulAttempts().items():
            if pattern_regex.search(username):
                result.append(dict(username=username, attempts=attempts))
        return result

    def manage_resetUsers(self, logins, RESPONSE=None):
        return self._getPlugin().manage_resetUsers(logins, RESPONSE=None)

    def manage_setSuccessfulLoginAttempt(self, login):
        return self._getPlugin().setSuccessfulAttempt(login)

    def manage_credentialsUpdated(self, username):
        """ register timestamp of last password change """
        return self._getPlugin().manage_credentialsUpdated(username)

    def manage_getPasswordChanges(self, min_days=0):
        """ Return history of password changes"""
        return self._getPlugin().manage_getPasswordChanges(min_days)

InitializeClass(LoginLockoutTool)
