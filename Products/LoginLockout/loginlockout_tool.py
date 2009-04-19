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

    def manage_resetUsers(self, logins, RESPONSE=None):
        return self._getPlugin().manage_resetUsers(logins, RESPONSE=None)

InitializeClass(LoginLockoutTool)
