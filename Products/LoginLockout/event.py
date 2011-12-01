from zope.component.interfaces import IObjectEvent, ObjectEvent
from zope.interface import implements


class IUserAccountLockedEvent(IObjectEvent):
    """ User account has been locked """


class IUserAccountUnlockedEvent(IObjectEvent):
    """ User account has been unlocked """


class UserAccountLockedEvent(ObjectEvent):
    """ User account has been locked """

    implements(IUserAccountLockedEvent)

    def __init__(self, object, login):
        self.login = login
        ObjectEvent.__init__(self, object)


class UserAccountUnlockedEvent(ObjectEvent):
    """ User account has been locked """

    implements(IUserAccountUnlockedEvent)

    def __init__(self, object, login):
        self.login = login
        ObjectEvent.__init__(self, object)
