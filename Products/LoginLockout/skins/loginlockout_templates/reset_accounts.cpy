## Controller Python Script "reset_accounts"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=
##
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName

# use the tool to proxy the plugin's methods
lltool = getToolByName(context, 'loginlockout_tool')

# Get a values from the form, convert to list if it's just one
user_ids = context.REQUEST.form.get('reset_users',[])
if not same_type(user_ids, []):
    user_ids = [user_ids,]
lltool.manage_resetUsers(user_ids)

# return to configlet
state.setNextAction('redirect_to:string:loginlockout_settings')

# give an informative message
context.plone_utils.addPortalMessage(
    _("Accounts were reset for these login names: %s" % ','.join(user_ids)))

return state

