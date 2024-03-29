import unittest
from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from transaction import commit
import doctest
from zope.component import getUtility, ComponentLookupError
from plone.app.testing import FunctionalTesting, TEST_USER_NAME
from plone.app.testing import IntegrationTesting
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
from plone.app.testing import PloneWithPackageLayer
from plone.testing import Layer, layered
try:
    from plone.testing.z2 import ZSERVER_FIXTURE
    from plone.testing.z2 import Browser
except ImportError:
    from plone.testing.zserver import ZSERVER_FIXTURE
    from plone.testing.zope import Browser
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
    bases=(FIXTURE, ZSERVER_FIXTURE),
    name='Products.LoginLockout:Functional',
)
ROBOT_TESTING = Layer(name='Products.LoginLockout:Robot')


def setUp(doctest):
    layer = doctest.globs['layer']
    app = layer['app']
    portal = layer['portal']

    def make_anon_browser(path=None):
        b = Browser(app)
        b.handleErrors = False
        if path:
            b.open(portal.absolute_url() + path)
        return b

    def make_admin_browser(path=None):
        b = Browser(app)
        b.addHeader('Authorization', 'Basic {}:{}'.format(SITE_OWNER_NAME, SITE_OWNER_PASSWORD))
        if path:
            b.open(portal.absolute_url() + path)
        else:
            b.open(portal.absolute_url())
        assert "personaltools-login" not in b.contents
        return b

    user_id = TEST_USER_NAME
    user_password = TEST_USER_PASSWORD

    base_id = SITE_OWNER_NAME
    base_password = SITE_OWNER_PASSWORD

    def config_property(**kw):
        for key, value in kw.items():
            try:
                registry = getUtility(IRegistry)
                settings = registry.forInterface(ILoginLockoutSettings, prefix="Products.LoginLockout")
                setattr(settings, key, value)
                continue
            except ComponentLookupError:
                pass
            try:
                p_tool = getToolByName(portal, 'portal_properties')
                p_tool.loginlockout_properties.setProperty(key, value)
                continue
            except AttributeError:
                raise
        commit()

    def get_loginlockout_settings():
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ILoginLockoutSettings, prefix="Products.LoginLockout")
        return settings

    doctest.globs.update(locals())
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
    portal.error_log._ignored_exceptions = ('Unauthorized',)

    def raising(self, info):
        import traceback
        traceback.print_tb(info[2])
        print(info[1])

    from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog
    SiteErrorLog.raising = raising


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(doctest.DocFileSuite(
            '../../README.rst', setUp=setUp,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE | doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS | doctest.IGNORE_EXCEPTION_DETAIL),
            layer=FUNCTIONAL_TESTING,
        ),
    ])
    return suite

# from zope.testing import doctestcase
# @doctestcase.doctestfiles('../../README.rst', optionflags=doctest.REPORT_ONLY_FIRST_FAILURE | doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
# class ReadmeTests(unittest.TestCase):
#     setUp = setUp


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
