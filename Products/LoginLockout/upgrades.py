# -*- coding: utf-8 -*-
from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from Products.LoginLockout.interfaces import ILoginLockoutSettings
from zope.component import getUtility

import logging

log = logging.getLogger('LoginLockout')


def migrate_portal_properties(portal):
    """ """
    p_tool = getToolByName(portal, 'portal_properties', None)
    loginlockout_properties = getattr(p_tool, 'loginlockout_properties', None)

    if loginlockout_properties is None:
        # nothing to migrate
        return

    loginlockout_registry = getUtility(IRegistry).forInterface(
        ILoginLockoutSettings,
        prefix='Products.LoginLockout')

    if loginlockout_registry is None:
        # nothing to migrate
        return

    setattr(loginlockout_registry, 'fake_client_ip', bool(loginlockout_properties.getProperty('fake_client_ip')))
    setattr(loginlockout_registry, 'reset_period', float(loginlockout_properties.getProperty('reset_period')))
    setattr(loginlockout_registry, 'max_attempts', int(loginlockout_properties.getProperty('max_attempts')))


def run_upgrade_2009031001_to_2018021801(context):
    """ """
    plone_root = aq_parent(aq_parent(context))
    log.info('Upgrade steps from version 20090310-01 to 20180218-01 is starting')

    log.info('values to be migrated `fake_client_ip, reset_period, reset_period`')

    migrate_portal_properties(plone_root)

    log.info('Upgrade has been done successfully')
