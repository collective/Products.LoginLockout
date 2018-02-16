# _*_ coding: utf-8 _*_
from .interfaces import ILoginLockoutSettings
from plone.app.registry.browser import controlpanel
from plone import api
from plone.app.iterate import PloneMessageFactory as _
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.utils import safe_hasattr
from zope.component import adapter
from zope.interface import implementer
from z3c.form import button
from zope.component import queryUtility


@adapter(IPloneSiteRoot)
@implementer(ILoginLockoutSettings)
class LoginLockoutSettingsAdapter(object):
    """ """
    def __init__(self, context):
        """ """
        self.context = context
        self.portal = api.portal.get()
        self.encoding = 'utf-8'
        registry = queryUtility(IRegistry)
        self.settings = registry.forInterface(
            ILoginLockoutSettings,
            prefix='Products.LoginLockout')

    @property
    def max_attempts(self):
        """ """
        return self.settings.max_attempts

    @max_attempts.setter
    def max_attempts(self, value):
        """ """
        if safe_hasattr(self.settings, 'max_attempts'):
            self.settings.max_attempts = value

    @property
    def reset_period(self):
        """ """
        return self.settings.reset_period

    @reset_period.setter
    def reset_period(self, value):
        """ """
        if safe_hasattr(self.settings, 'reset_period'):
            self.settings.reset_period = value

    @property
    def whitelist_ips(self):
        """ """
        return self.settings.whitelist_ips

    @whitelist_ips.setter
    def whitelist_ips(self, value):
        """ """
        if safe_hasattr(self.settings, 'whitelist_ips'):
            self.settings.whitelist_ips = value

    @property
    def fake_client_ip(self):
        """ """
        return self.settings.fake_client_ip

    @fake_client_ip.setter
    def fake_client_ip(self, value):
        """ """
        if safe_hasattr(self.settings, 'fake_client_ip'):
            self.settings.fake_client_ip = value


class LoginLockoutSettingsForm(controlpanel.RegistryEditForm):

    id = 'LoginLockoutSettings'
    label = _(u'LoginLockout Settings')
    schema = ILoginLockoutSettings
    schema_prefix = 'Products.LoginLockout'

    @button.buttonAndHandler(_('Save'), name=None)
    def handleSave(self, action):
        self.save()

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        super(LoginLockoutSettingsForm, self).handleCancel(self, action)

    def save(self):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return False

        self.applyChanges(data)
        return True


class LoginLockoutSetting(controlpanel.ControlPanelFormWrapper):
    form = LoginLockoutSettingsForm
