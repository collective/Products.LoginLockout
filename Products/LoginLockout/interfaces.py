from zope import schema
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface

_ = MessageFactory('LoginLockout')


class ILoginLockoutSettings(Interface):

    max_attempts = schema.Int(
        title=_(u'Max Attempts'),
        description=_(u'Number of unsuccessful logins before account locked'),
        default=3,
        required=True
    )

    reset_period = schema.Float(
        title=_(u'Reset Period (hours)'),
        description=_(u'Locked accounts are reenabled after this time'),
        default=24.0,
        required=True
    )

    whitelist_ips = schema.Text(
        title=_(u'Lock logins to IP Ranges'),
        description=_(u'List of IP Ranges which Client IP must be in to login. Empty disables'),
        default=u'',
        required=False
    )

    fake_client_ip = schema.Bool(
        title=_(u'Fake Client IP'),
        description=_(u'Ignore X-Forward-For and REMOTE_ADDR headers'),
        default=False,
        required=False
    )
