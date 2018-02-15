
import unittest

from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from transaction import commit
from zope.testing import doctest
from zope.testing import doctestunit
from zope.component import testing, getUtility, ComponentLookupError
#import DateTime
#from DateTime.interfaces import DateTimeError, SyntaxError, DateError, TimeError
#from plone.login.interfaces import IPloneLoginLayer
# -*- coding: utf-8 -*-
from plone.app.testing import FunctionalTesting, TEST_USER_NAME
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID, TEST_USER_PASSWORD
from plone.app.testing import PloneWithPackageLayer
from plone.testing import Layer, layered
from plone.testing.z2 import Browser, installProduct
from plone.testing.z2 import ZSERVER_FIXTURE
#from Testing.ZopeTestCase import FunctionalTestCase
#from transaction import commit
#from unittest2 import TestCase
import Products.LoginLockout
from Products.LoginLockout.interfaces import ILoginLockoutSettings

FIXTURE = PloneWithPackageLayer(
    zcml_package=Products.LoginLockout,
    zcml_filename='configure.zcml',
    gs_profile_id='Products.LoginLockout:default',
    name="LoginLockoutFixture",
)

INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name='Products.LoginLockout:Integration',
)
FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE,ZSERVER_FIXTURE),
    name='Products.LoginLockout:Functional',
)
ROBOT_TESTING = Layer(name='Products.LoginLockout:Robot')

def setUp(doctest):
    layer = doctest.globs['layer']
    app = layer['app']
    portal = layer['portal']
    anon_browser = Browser(app)
    admin_browser = Browser(app)
    admin_browser.addHeader('Authorization', 'Basic admin:secret')

    #self.portal_url = 'http://nohost/plone'
    user_id = TEST_USER_NAME
    user_password = TEST_USER_PASSWORD

    def config_property(**kw):
        #admin_browser.open(portal.absolute_url() + '/acl_users/login_lockout_plugin/manage_propertiesForm')
        #admin_browser.getControl(name='_whitelist_ips:lines').value = range
        #admin_browser.getControl(name='manage_editProperties:method').click()
        for key,value in kw.items():
            try:
                registry = getUtility(IRegistry)
                settings = registry.forInterface(ILoginLockoutSettings)
                setattr(settings, key, value)
                return
            except ComponentLookupError:
                pass
            try:
                p_tool = getToolByName(portal, 'portal_properties')
                p_tool.loginlockout_properties.setProperty(key, value)
                return
            except AttributeError:
                raise
        commit()

    doctest.globs.update(locals())
    #alsoProvides(self.request, IPloneFormLayer)
    #alsoProvides(self.request, IPloneLoginLayer)
    #self.afterSetUp()
    #commit()
#
#     def afterSetUp(self):
#        # sm = getSiteManager(context=self.portal)
#         # sm.unregisterUtility(provided=IMailHost)
#         # sm.registerUtility(mailhost, provided=IMailHost)
#     #
#     # def setStatusCode(self, key, value):
#     #     from ZPublisher import HTTPResponse
#     #     HTTPResponse.status_codes[key.lower()] = value
#
    anon_browser.handleErrors = False
    portal.error_log._ignored_exceptions = ('Unauthorized',)

    def raising(self, info):
        import traceback
        traceback.print_tb(info[2])
        print info[1]

    from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog
    SiteErrorLog.raising = raising

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(doctest.DocFileSuite(
            '../../README.rst',setUp = setUp,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE |
                        doctest.NORMALIZE_WHITESPACE |
                        doctest.ELLIPSIS),
        layer=FUNCTIONAL_TESTING,
        ),
    ])
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
