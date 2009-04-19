from plugin import PROJECTNAME

TOOL_ID = "loginlockout_tool"

CONFIGLETS = (
    {
        'id'         : 'LoginLockoutConf',
        'name'       : 'LoginLockout',
        'action'     : 'string:${portal_url}/loginlockout_settings',
        'condition'  : '',
        'category'   : 'Products',
        # section to which the configlet should be added:
        # (Plone,Products,Members)
        'visible'    : 1,
        'appId'      : PROJECTNAME,
        'permission' : 'ManagePortal',
        'imageUrl'   : 'lock_icon.gif',
    },   
) 
