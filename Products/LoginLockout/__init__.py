from AccessControl.Permissions import add_user_folders
from Products.CMFCore import utils
from Products.LoginLockout.loginlockout_tool import LoginLockoutTool
from Products.LoginLockout.plugin import PROJECTNAME
from Products.PluggableAuthService import registerMultiPlugin
from Products.LoginLockout.plugin import LoginLockout
from Products.LoginLockout.plugin import manage_addLoginLockout
from Products.LoginLockout.plugin import manage_addLoginLockoutForm

"""LoginLockout
"""

__author__ = "Dylan Jay <software@pretaweb.com>"


def initialize(context):
    """Initialize the LoginLockout plugin.
    Register skin directory.
    """
    registerMultiPlugin(LoginLockout.meta_type)

    context.registerClass(LoginLockout,
                          permission=add_user_folders,
                          constructors=(manage_addLoginLockoutForm,
                                        manage_addLoginLockout),
                          icon='www/tool.gif',
                          visibility=None,
                          )

    # register the tool
    tools = (LoginLockoutTool,)
    utils.ToolInit(
        PROJECTNAME,
        icon='www/tool.gif',
        tools=tools).initialize(context)
