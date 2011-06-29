## Controller Python Script "logged_in"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=new_password
##title=Initial post-login actions
##

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
REQUEST=context.REQUEST

membership_tool=getToolByName(context, 'portal_membership')
if membership_tool.isAnonymousUser():
    REQUEST.RESPONSE.expireCookie('__ac', path='/')
    email_login = getToolByName(
        context, 'portal_properties').site_properties.getProperty('use_email_as_login')
    if email_login:
        context.plone_utils.addPortalMessage(_(u'Login failed. Both email address and password are case sensitive, check that caps lock is not enabled.'), 'error')
    else:
        context.plone_utils.addPortalMessage(_(u'Login failed. Both login name and password are case sensitive, check that caps lock is not enabled.'), 'error')
    return state.set(status='failure')

member = membership_tool.getAuthenticatedMember()
# removed initial_login and must_change_password code (which was copied from
# original login_form), because user has to be logged in at least once already

membership_tool.loginUser(REQUEST)
# do not change password if user don't need to change it
if context.loginlockout_tool.get_must_change_password():
    try:
        membership_tool.setPassword(new_password)
    except AttributeError:
        context.plone_utils.addPortalMessage(_(u'While changing your password an AttributeError occurred. This is usually caused by your user being defined outside the portal.'), 'error')
        return state.set(status='failure')

    context.credentials_updated(member.getUserName())
    member.setProperties(must_change_password=0)

    from Products.CMFPlone.utils import transaction_note
    transaction_note('Changed password for %s' % (member.getUserName()))

return state
