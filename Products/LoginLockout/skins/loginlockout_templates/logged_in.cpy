## Controller Python Script "logged_in"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=Initial post-login actions
##

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
REQUEST=context.REQUEST

membership_tool=getToolByName(context, 'portal_membership')
if membership_tool.isAnonymousUser():
    REQUEST.RESPONSE.expireCookie('__ac', path='/')
    context.plone_utils.addPortalMessage(_(u'Login failed. Both login name and password are case sensitive, check that caps lock is not enabled.'), 'error')
    return state.set(status='failure')

member = membership_tool.getAuthenticatedMember()
login_time = member.getProperty('login_time', '2000/01/01')
initial_login = int(str(login_time) == '2000/01/01')
state.set(initial_login=initial_login)

must_change_password = member.getProperty('must_change_password', 0)
state.set(must_change_password=must_change_password)

if initial_login:
    state.set(status='initial_login')
    # if user is logged-in for the first time, set-up initial
    # password change date to be able to count password expiration period
    context.credentials_updated(member.getUserName())
elif must_change_password:
    state.set(status='change_password')

membership_tool.loginUser(REQUEST)
if context.loginlockout_tool.get_must_change_password():
    membership_tool.logoutUser(REQUEST)
    state.set(status='expired_password', login_name=member.getUserName(), must_change_password=1)
context.setSuccessfulLoginAttempt(member.getUserName())
return state
