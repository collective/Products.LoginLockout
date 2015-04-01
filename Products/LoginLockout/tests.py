from Products.Five import fiveconfigure
from Products.Five import zcml
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
from Testing import ZopeTestCase as ztc
from zope.testing import doctest
import unittest

print "Start installProduct"
ztc.installProduct('LoginLockout')
print "Finished installProduct setup (hopefully)"


class TestCase(ptc.PloneTestCase):
    """ We use this base class for all the tests in this package. If necessary,
        we can put common utility or setup code in here. This applies to unit
        test cases. """
    _configure_portal = False

    def beforeTearDown(self):
        pass

    def afterSetUp(self):

        self.portal.acl_users.portal_role_manager.updateRolesList()

        self.portal.acl_users._doAddUser('admin', 'admin', ('Manager',), [])
        self.portal.acl_users._doAddUser('user', 'user', ('Member',), [])

        self.portal.error_log._ignored_exceptions = ()


@onsetup
def setup_product():
    """ """
    fiveconfigure.debug_mode = True
    import Products.LoginLockout
    zcml.load_config('configure.zcml', Products.LoginLockout)
    fiveconfigure.debug_mode = False


ztc.installProduct('Products.LoginLockout')
setup_product()
ptc.setupPloneSite(
    extension_profiles=(),
    with_default_memberarea=False,
    products=['Products.LoginLockout'])


def test_suite():
    return unittest.TestSuite([
        # USE CASES
        ztc.FunctionalDocFileSuite(
            usecase,
            package='Products.LoginLockout',
            test_class=TestCase,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE |
            doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS,
        )
        for usecase in [
            'README.txt',
        ]

    ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
