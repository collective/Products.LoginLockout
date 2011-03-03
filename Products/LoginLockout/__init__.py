"""LoginLockout
"""

__author__ = "Dylan Jay <software@pretaweb.com>"

from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from plugin import LoginLockout, \
                   manage_addLoginLockout, \
                   manage_addLoginLockoutForm

from Products.CMFCore.DirectoryView import registerDirectory

from Products.CMFCore import utils
from Products.LoginLockout.plugin import PROJECTNAME
from Products.LoginLockout.loginlockout_tool import LoginLockoutTool

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

    # register the custom skins directory
    GLOBALS = globals()
    registerDirectory('skins', GLOBALS)

    # register the tool
    tools = ( LoginLockoutTool, )
    utils.ToolInit(
        PROJECTNAME,
        icon='www/tool.gif',
        tools=tools).initialize(context)

