from zope import schema
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

_ = MessageFactory('LoginLockout')


class ILoginLockoutSettings(Interface):

    max_attempts = schema.Int(
        title=_('Max Attempts'),
        description=_('Number of unsuccessful logins before account locked'),
        default=3,
        required=True
    )

    reset_period = schema.Float(
        title=_('Reset Period (hours)'),
        description=_('Locked accounts are reenabled after this time'),
        default=24.0,
        required=True
    )

    whitelist_ips = schema.Text(
        title=_('Lock logins to IP Ranges'),
        description=_('List of IP Ranges which Client IP must be in to login. Empty disables'),
        default='',
        required=False
    )

    fake_client_ip = schema.Bool(
        title=_('Fake Client IP'),
        description=_('Ignore X-Forward-For and REMOTE_ADDR headers'),
        default=False,
        required=False
    )


class ILoginLockoutLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""
