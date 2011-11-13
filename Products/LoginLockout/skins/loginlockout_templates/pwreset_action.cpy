## Script (Python) "pwreset_action.cpy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##title=Reset a user's password
##parameters=randomstring, userid=None, password=None, password2=None
from Products.CMFCore.utils import getToolByName

status = "success"
pw_tool = getToolByName(context, 'portal_password_reset')
try:
    pw_tool.resetPassword(userid, randomstring, password)
    # added for ITIS
    mt=context.portal_membership
    member = mt.getMemberById(userid)
    context.credentials_updated(member.getUserName())
except 'ExpiredRequestError':
    status = "expired"
except 'InvalidRequestError':
    status = "invalid"
except RuntimeError:
    status = "invalid"

return state.set(status=status)

