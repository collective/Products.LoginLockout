from Products.PluggableAuthService.events import CredentialsUpdated
from zope.event import notify


# TODO: ensure only happens before 5.2
def doChangeUser(self, principal_id, password):
    result = self._old_doChangeUser(principal_id, password)
    # before plone 5.2 we this event wasn't emited so we need to do this
    notify(CredentialsUpdated(self.getUserById(principal_id), password))
    return result


# # Fix bug in Products/PluggableAuthService/events
# # This is a cleaner patch the one below but doesn't work because of the @adapter call
# def userCredentialsUpdatedHandler(principal, event):
#     pas = aq_parent(principal)
#     pas.updateCredentials(
#         pas.REQUEST,
#         pas.REQUEST.RESPONSE,
#         principal.getId(),
#         event.password)


# Fix bug where Products/PluggableAuthService/events/userCredentialsUpdatedHandler calls
# with wrong arguments
# Can;t patch events.userCredentialsUpdatedHandler directly for some reason
def updateCredentials(self, request, response, login, new_password, extra=None):
    if extra is not None:
        request, response, login, new_password = response, login, new_password, extra
    return self._old_updateCredentials(request, response, login, new_password)


# Bug in this on 4.1 where it should call authenticate with the username not userid
def testCurrentPassword(self, password):
    """ test to see if password is current """
    REQUEST = getattr(self, 'REQUEST', {})
    userid = self.getAuthenticatedMember().getUserId()
    acl_users = self._findUsersAclHome(userid)
    if not acl_users:
        return 0
    return acl_users.authenticate(self.getAuthenticatedMember().getUserName(), password, REQUEST)
