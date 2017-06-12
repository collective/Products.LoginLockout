
import unittest

from zope.testing import doctest
from zope.testing import doctestunit
from zope.component import testing
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
from plone.testing.z2 import Browser
from plone.testing.z2 import ZSERVER_FIXTURE
#from Testing.ZopeTestCase import FunctionalTestCase
#from transaction import commit
#from unittest2 import TestCase
import Products.LoginLockout





# @onsetup
# def setup_product():
#     """ """
#     fiveconfigure.debug_mode = True
#     import Products.LoginLockout
#     zcml.load_config('configure.zcml', Products.LoginLockout)
#     fiveconfigure.debug_mode = False

#
#ztc.installProduct('Products.LoginLockout')
#setup_product()
# ptc.setupPloneSite(extension_profiles=(), with_default_memberarea=False,
#         products=['Products.LoginLockout'])
#
#
# print "Start installProduct"
# ztc.installProduct('LoginLockout')
# print "Finished installProduct setup (hopefully)"

# class TestCase(ptc.PloneTestCase):
#     """ We use this base class for all the tests in this package. If necessary,
#         we can put common utility or setup code in here. This applies to unit
#         test cases. """
#     _configure_portal = False
#
#     def beforeTearDown(self):
#         pass
#
#     def afterSetUp(self):
#
#         self.portal.acl_users.portal_role_manager.updateRolesList()
#
#         self.portal.acl_users._doAddUser('admin', 'admin', ('Manager',), [])
#         self.portal.acl_users._doAddUser('user', 'user', ('Member',), [])
#
#         self.portal.error_log._ignored_exceptions = ()



class Fixture(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

#     def setUpZope(self, app, configurationContext):
#         # Load ZCML
#         import Products.LoginLockout
#         self.loadZCML(
#             package=Products.LoginLockout, context=configurationContext)
#
#     def setUpPloneSite(self, portal):
#         self.applyProfile(portal, 'Products.LoginLockout:default')
#         portal.acl_users.userFolderAddUser('admin',
#                                            'secret',
#                                            ['Manager'],
#                                            [])
#         login(portal, 'admin')
#         setRoles(portal, TEST_USER_ID, ['Manager'])
#         portal.manage_changeProperties(
#             **{'email_from_address': 'mdummy@address.com'})
#

#FIXTURE = Fixture()

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

#
# class LoginLockoutTestCase(TestCase):
#
#     layer = INTEGRATION_TESTING
#
#     def setUp(self):
#         self.app = self.layer['app']
#         self.portal = self.layer['portal']
#         #self.portal.invokeFactory('Folder', 'test-folder')
#         #self.folder = self.portal['test-folder']
#         self.afterSetUp()
#
#     def afterSetUp(self):
#         pass
#
#
# class LoginLockoutFunctionalTestCase(FunctionalTestCase):
#
#     layer = FUNCTIONAL_TESTING
#
def setUp(doctest):
    #self.app = self.layer['app']
    #self.portal.invokeFactory('Folder', 'news')
    layer = doctest.globs['layer']
    app = layer['app']
    portal = layer['portal']
    anon_browser = Browser(app)
    admin_browser = Browser(app)
    admin_browser.addHeader('Authorization', 'Basic admin:secret')

    #self.portal_url = 'http://nohost/plone'
    user_id = TEST_USER_NAME
    user_password = TEST_USER_PASSWORD
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
            'README.txt',setUp = setUp,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE |
                        doctest.NORMALIZE_WHITESPACE |
                        doctest.ELLIPSIS),
        layer=FUNCTIONAL_TESTING,
        ),
    ])
    return suite

#
# def test_suite():
#     return unittest.TestSuite([
#         # USE CASES
#         ztc.FunctionalDocFileSuite(
#             usecase , package='Products.LoginLockout',
#             test_class=LoginLockoutFunctionalTestCase,
#             optionflags=doctest.REPORT_ONLY_FIRST_FAILURE |
#                         doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
#             for usecase in ['README.txt',
#                            ]
#
#         ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
