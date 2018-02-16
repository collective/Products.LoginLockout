from zope import schema
from zope.interface import Interface
from plone.app.iterate import PloneMessageFactory as _


class ILoginLockoutSettings(Interface):

    max_attempts = schema.Int(
        title=_(u'Max Attempts'),
        description=u'Number of unsuccessful logins before account locked',
        default=3,
        required=True
    )

    reset_period = schema.Float(
        title=_(u'Reset Period (hours)'),
        description=u'Locked accounts are reenabled after this time',
        default=24.0,
        required=True
    )

    whitelist_ips = schema.Text(
        title=_(u'Lock logins to IP Ranges'),
        description=u'List of IP Ranges which Client IP must be in to login. Empty disables',
        default=u'',
        required=False
    )

    fake_client_ip = schema.Bool(
        title=_(u'Fake Client IP'),
        description=u'Ignore X-Forward-For and REMOTE_ADDR headers',
        default=False,
        required=False
    )
