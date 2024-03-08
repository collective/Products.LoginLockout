# -*- coding: utf-8 -*-

from Products.Five import BrowserView
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName
try:
    from plone.base.utils import safe_text
except ImportError:
    from Products.CMFPlone.utils import safe_unicode as safe_text
from Products.statusmessages.interfaces import IStatusMessage


class LockoutsView(BrowserView):
    """ View locked accounts
    """

    def __call__(self):
        """ Method to reset accounts """

        # if not reset_ploneusers and not reset_nonploneusers:
        #     return

        # Get a values from the form, convert to list if it's just one
        user_ids = self.request.form.get('reset_ploneusers', [])
        user_ids += self.request.form.get('reset_nonploneusers', [])
        if type(user_ids) is not list:
            user_ids = [user_ids, ]

        if user_ids:
            # use the tool to proxy the plugin's methods
            lltool = getToolByName(self, 'loginlockout_tool')
            lltool.manage_resetUsers(user_ids)

            # # return to configlet
            # state.setNextAction('redirect_to:string:loginlockout_settings')

            # give an informative message
            messages = IStatusMessage(self.request)
            messages.add(_("Accounts were reset for these login names: %s" % safe_text(','.join(user_ids))), type=u"info")
        return self.index()


class HistoryView(BrowserView):
    """ View locked accounts
    """

    # def credentials_updated(self, username):
    #     """ Reset credentials """
    #     self.loginlockout_tool.manage_credentialsUpdated(username)
    #     return self.index()
