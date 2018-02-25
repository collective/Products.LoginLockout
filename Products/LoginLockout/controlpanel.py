# _*_ coding: utf-8 _*_
from .interfaces import ILoginLockoutSettings
from plone.app.registry.browser import controlpanel
from plone.app.iterate import PloneMessageFactory as _
from z3c.form import form
from plone.z3cform import layout


class LoginLockoutSettingsForm(controlpanel.RegistryEditForm):

    schema = ILoginLockoutSettings
    schema_prefix = 'Products.LoginLockout'
    form.extends(controlpanel.RegistryEditForm)


LoginLockoutSetting = layout.wrap_form(LoginLockoutSettingsForm, controlpanel.ControlPanelFormWrapper)
LoginLockoutSetting.label = _(u'LoginLockout Settings')
