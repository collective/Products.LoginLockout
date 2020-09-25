from Products.CMFCore.utils import getToolByName
from Products.LoginLockout.plugin import PLUGIN_ID, manage_addLoginLockout
from Products.LoginLockout.plugin import PLUGIN_TITLE
from Products.LoginLockout.plugin import PROJECTNAME
from Products.LoginLockout.plugin import log
from io import StringIO


def install(portal):

    """ This plugin needs to be installed in two places, the instance PAS where
    logins occur and the root acl_users.

    Different interfaces need to be activated for either case.
    """
    out = StringIO()
    out.write("Installing %s:" % PROJECTNAME)

    plone_pas = getToolByName(portal, 'acl_users')
    zope_pas = portal.getPhysicalRoot().acl_users

    # define the interfaces which need to be activated for either PAS
    interfaces_for_paservices = {
        plone_pas: ['IAuthenticationPlugin', 'IChallengePlugin',
                    'ICredentialsUpdatePlugin'],
        zope_pas: ['IChallengePlugin', 'IAnonymousUserFactoryPlugin'],
    }
    for (pas, interfaces) in interfaces_for_paservices.items():
        existing = pas.objectIds()
        if PLUGIN_ID not in existing:
            loginlockout = pas.manage_addProduct[PROJECTNAME]
            manage_addLoginLockout(loginlockout, PLUGIN_ID, PLUGIN_TITLE)
            activatePluginSelectedInterfaces(pas, PLUGIN_ID, out, interfaces)

    # define which interfaces need to be moved to top of plugin list
    move_to_top_for = {
        plone_pas: 'IChallengePlugin',
        zope_pas: 'IAnonymousUserFactoryPlugin',
    }
    for (pas, interface) in move_to_top_for.items():
        movePluginToTop(pas, PLUGIN_ID, interface, out)

    # install configlet

    out.write("Successfully installed %s:" % PROJECTNAME)
    return out.getvalue()


def uninstall(portal):
    out = StringIO()
    out.write("Uninstalling %s:" % PROJECTNAME)
    plone_pas = getToolByName(portal, 'acl_users')
    # TODO: probably shouldn't delete zope plugin because it can break other sites. Leave it but make sure it doesn't do anything
    # - but leaving the plugin would break the site if package goes away?
    zope_pas = portal.getPhysicalRoot().acl_users
    for pas in [plone_pas, zope_pas]:
        existing = pas.objectIds()
        if PLUGIN_ID in existing:
            pas.manage_delObjects(PLUGIN_ID)


def activatePluginSelectedInterfaces(
        pas, plugin, out, selected_interfaces, disable=[]):
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
                out.write(" - Disabling: " + info['title'])
            else:
                activatable.append(interface_name)
                out.write(" - Activating: " + info['title'])
    plugin_obj.manage_activateInterfaces(activatable)
    out.write(plugin + " activated.")


def movePluginToTop(pas, plugin_id, interface_name, out):
    """This moves a plugin to the top of the plugins list
    for a given interface.
    """
    registry = pas.plugins
    interface = registry._getInterfaceFromName(interface_name)
    while registry.listPlugins(interface)[0][0] != plugin_id:
        registry.movePluginsUp(interface, [plugin_id])
    out.write(
        "Moved " + plugin_id + " to top in " + interface_name + "."
    )


def setupVarious(context):
    """Import step for configuration that is not handled in xml files.
    """
    # Only run step if a flag file is present
    if context.readDataFile('loginlockout.txt') is None:
        return

    site = context.getSite()
    install(site)


def uninstallVarious(context):
    """"""
    # Only run step if a flag file is present
    if context.readDataFile('loginlockout_uninstall.txt') is None:
        return
    log.info('LoginLockout uninstall process is starting...')
    # may be plugin uninstall here?
    site = context.getSite()
    if 'loginlockout_properties' in site.portal_properties:
        site.portal_properties.manage_delObjects(ids=['loginlockout_properties'])
    uninstall(site)
