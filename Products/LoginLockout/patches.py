

def setPassword(self, password, domains=None, REQUEST=None):
    result = self._old_setPassword(password, domains, REQUEST)
    member = self.getAuthenticatedMember()
    # TODO: check if its username or userid
    self.credentials_updated(member.getUserId())
    return result
