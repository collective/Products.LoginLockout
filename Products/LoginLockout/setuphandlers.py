from StringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
from Products.LoginLockout.plugin import PROJECTNAME, PLUGIN_ID, PLUGIN_TITLE
from Products.CMFCore.permissions import ManagePortal

# for adding tool
from Products.LoginLockout.config import TOOL_ID, CONFIGLETS

def install(portal):

    """ This plugin needs to be installed in two places, the instance PAS where
    logins occur and the root acl_users.

    Different interfaces need to be activated for either case.
    """
    out = StringIO()
    print >> out, "Installing %s:" % PROJECTNAME

    plone_pas = getToolByName(portal, 'acl_users')
    zope_pas = portal.getPhysicalRoot().acl_users

    # define the interfaces which need to be activated for either PAS
    interfaces_for_paservices = {
        plone_pas: ['IAuthenticationPlugin','IChallengePlugin',
                'ICredentialsUpdatePlugin'],
        zope_pas: ['IChallengePlugin','IAnonymousUserFactoryPlugin'],
        }
    for (pas, interfaces) in interfaces_for_paservices.iteritems():
        registry = pas.plugins
        existing = pas.objectIds()
        if PLUGIN_ID not in existing:
            loginlockout = pas.manage_addProduct[PROJECTNAME]
            loginlockout.manage_addLoginLockout(PLUGIN_ID, PLUGIN_TITLE)
            activatePluginSelectedInterfaces(pas, PLUGIN_ID, out, interfaces)

    # define which interfaces need to be moved to top of plugin list
    move_to_top_for = {
        plone_pas: 'IChallengePlugin',
        zope_pas: 'IAnonymousUserFactoryPlugin',
        }
    for (pas, interface) in move_to_top_for.iteritems():
        movePluginToTop(pas, PLUGIN_ID, interface, out)
    

    # add tool
    addTool(portal, PROJECTNAME, TOOL_ID)

    # install configlet
    installConfiglets(portal, out, CONFIGLETS)

    print >> out, "Successfully installed %s." % PROJECTNAME
    return out.getvalue()

def uninstall( portal ):
    out = StringIO()
    print >> out, "Uninstalling %s:" % PROJECTNAME
    plone_pas = getToolByName(portal, 'acl_users')
    zope_pas = portal.getPhysicalRoot().acl_users
    for pas in [plone_pas, zope_pas]:
        existing = pas.objectIds()
        if PLUGIN_ID in existing:
            pas.manage_delObjects(PLUGIN_ID)

    # uninstall configlets
    installConfiglets(portal, out, CONFIGLETS, uninstall=True)

def activatePluginSelectedInterfaces(pas, plugin, out, selected_interfaces, 
        disable=[]):
    """This is derived from PlonePAS's activatePluginInterfaces, but 
    will only activate the plugin for selected interfaces. 
    
    For LoginLockout, you'll want to activate different interfaces for 
    different PAS instances.

    The PAS instance (either Plone's or Zope's) in which to activate the 
    interfaces is passed as an argument, so portal is not needed.
    """
    plugin_obj = pas[plugin]
    activatable = []
    for info in plugin_obj.plugins.listPluginTypeInfo():
        interface = info['interface']
        interface_name = info['id']
        if plugin_obj.testImplements(interface) and \
                interface_name in selected_interfaces:
            if interface_name in disable:
                disable.append(interface_name)
                print >> out, " - Disabling: " + info['title']
            else:
                activatable.append(interface_name)
                print >> out, " - Activating: " + info['title']
    plugin_obj.manage_activateInterfaces(activatable)
    print >> out, plugin + " activated."

def movePluginToTop(pas, plugin_id, interface_name, out):
    """This moves a plugin to the top of the plugins list
    for a given interface.
    """
    registry = pas.plugins
    interface = registry._getInterfaceFromName(interface_name)
    while registry.listPlugins(interface)[0][0] != plugin_id:
        registry.movePluginsUp(interface,[plugin_id,])
    print >> out, "Moved " + plugin_id + " to top in " + interface_name + "."

def addTool(portal, product_name, tool_id):
    try:
        ctool = getToolByName(portal, tool_id)
    except AttributeError:
        portal.manage_addProduct[product_name].manage_addTool(product_name, 
                None)

def installConfiglets(portal, out, configlets, uninstall=False):

    """
    Install a configlet for the plone site. configlets parameter should be a 
    list of hashes.
    """

    print >> out, 'Installing configlet...'

    ctool = getToolByName(portal, 'portal_controlpanel')

    for c in configlets:
        print >> out, "-> installing configlet %s" % c['name']
        ctool.unregisterConfiglet(c['id'])
        if not uninstall:
            ctool.registerConfiglet(**c)

    print >> out, "done."


def setupVarious(context):
    """Import step for configuration that is not handled in xml files.
    """
    # Only run step if a flag file is present
    if context.readDataFile('loginlockout.txt') is None:
        return

    logger = context.getLogger('Products.LoginLockout')
    site = context.getSite()
    install(site)
