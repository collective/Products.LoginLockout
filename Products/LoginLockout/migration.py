from Products.CMFCore.utils import getToolByName
from Products.LoginLockout.plugin import PLUGIN_ID

import logging
logger = logging.getLogger('Upgrade LoginLockout')

def migrateTo04(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    plone_pas = getToolByName(portal, 'acl_users')
    zope_pas = portal.getPhysicalRoot().acl_users
    
    for pas in (plone_pas, zope_pas):
        plugin = getattr(pas, PLUGIN_ID, None)
        if plugin is not None:
            attr = getattr(plugin, '_password_expire_period', None)
            if attr is None:
                setattr(plugin, '_password_expire_period', 0)
                logger.info('%s - added _password_expire_period attribute', '/'.join(pas.getPhysicalPath()))
                # set "last password change" to all users which has not changed password yet
                # we want all users to change their password after _password_expire_period at least
                count = 0
                for username in pas.getUserNames():
                    if plugin._last_pw_change.get(username, None) is None:
                        plugin.manage_credentialsUpdated(username)
                        count += 1
                logger.info('%s - initialized _last_pw_change property for %d users.', '/'.join(pas.getPhysicalPath()), count)
            else:
                logger.info('%s - already migrated', '/'.join(pas.getPhysicalPath()))


    
    