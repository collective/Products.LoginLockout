# _*_ coding: utf-8 _*_
from plone.app.registry.browser import controlpanel
from plone.z3cform import layout
from Products.LoginLockout.interfaces import _
from Products.LoginLockout.interfaces import ILoginLockoutSettings
from z3c.form import form


class LoginLockoutSettingsForm(controlpanel.RegistryEditForm):

    schema = ILoginLockoutSettings
    schema_prefix = 'Products.LoginLockout'
    form.extends(controlpanel.RegistryEditForm)


LoginLockoutSetting = layout.wrap_form(LoginLockoutSettingsForm, controlpanel.ControlPanelFormWrapper)
LoginLockoutSetting.label = _(u'LoginLockout Settings')
