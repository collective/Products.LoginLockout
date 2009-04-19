LoginLockout
============

This Pluggable Authentication Service (PAS) plugin will lock a
login after a predetermined number of incorrect attempts. Once
locked, the user will be shown a page that tells them to contact
their administrator to unlock.

Requires:
---------

- PluggableAuthService and its dependencies

- (optional) PlonePAS and its dependencies


Details
-------
LoginLockout can be used as a Plone plugin or with zope and PAS alone.
First we'll show you how it works with Plone.

To Install

First login as manager

	>>> from Products.Five.testbrowser import Browser
	>>> admin = Browser(self.portal.absolute_url()+'/login_form')
	>>> admin.getControl('Login Name').value = 'admin'
	>>> admin.getControl('Password').value = 'admin'
	>>> admin.getControl('Log in').click()

 go to Site Setup > Add-on Products and install LoginLockout.

	>>> admin.getLink('Site Setup').click()
	>>> admin.getLink('Add-on Products').click()
	>>> admin.getControl("LoginLockout 0.1 svn/dev installer branch").click()
	>>> admin.getControl('Install').click()

	>>> admin.getLink(url="LoginLockout/prefs_installed_product_overview").click()
	>>> print admin.contents
	<BLANKLINK>
	...
	Installing LoginLockout:
	- Activating: authentication
	- Activating: challenge
	- Activating: update credentials
	login_lockout_plugin activated.
	- Activating: anonymoususerfactory
	- Activating: challenge
	login_lockout_plugin activated.
	Moved login_lockout_plugin to top in IChallengePlugin.
	Moved login_lockout_plugin to top in IAnonymousUserFactoryPlugin.
	Successfully installed LoginLockout.
	...

	>>> admin.goBack()


Now we'll open up a new browser and attempt to login


	>>> browser = Browser()
	>>> browser.open(self.portal.absolute_url()+'/login_form')
	>>> browser.getControl('Login Name').value = 'user'
	>>> browser.getControl('Password').value = 'user'
	>>> browser.getControl('log in').click()
	>>> print browser.contents
	You have succesfully logged in

Let's try again with another password

	>>> browser = Browser()
	>>> browser.open(self.portal.absolute_url()+'/login_form')
	>>> browser.getControl('Login Name').value = 'user'
	>>> browser.getControl('Password').value = 'notpassword'
	>>> browser.getControl('log in').click()
	>>> print browser.contents
	Password incorrect

this incorrect attemp  will show up in the log

	>>> admin.getLink('Site Setup').click()
	>>> admin.getLink('LoginLockup').click()
	>>> print admin.contents
	user attemps 1

If we try twice more we will be locked out

	>>> browser.getControl('Login Name').value = 'user'
	>>> browser.getControl('Password').value = 'notpassword2'
	>>> browser.getControl('log in').click()
	>>> browser.getControl('Password').value = 'notpassword3'
	>>> browser.getControl('log in').click()
	>>> print admin.contents
	You have been locked out. Please contact the system administrator

Now even the correct password won't work

	>>> browser.open(self.portal.absolute_url()+'/login_form')
	>>> browser.getControl('Login Name').value = 'user'
	>>> browser.getControl('Password').value = 'user'
	>>> browser.getControl('log in').click()
	>>> print browser.contents
	You have been locked out. Please contact the system administrator

The administrator can reset this persons account

	>>> admin.getLink('Site Setup').click()
	>>> admin.getLink('LoginLockup').click()
	>>> print admin.contents
	user attemps 4
	>>> admin.getControl('user').click()
	>>> admin.getControl('reset accounts').click()
	>>> print admin.contents
	...User accounts reset...

and now they can log in again

	>>> browser.open(self.portal.absolute_url()+'/login_form')
	>>> browser.getControl('Login Name').value = 'user'
	>>> browser.getControl('Password').value = 'user'
	>>> browser.getControl('log in').click()
	>>> print browser.contents
	You have logged in


Manual Installation
-------------------

This plugin needs to be installed in two places, the instance PAS where logins
occur and the root acl_users.

1. Place the Product directory 'LoginLockout' in your 'Products/'
directory. Restart Zope.

2. In your instance PAS 'acl_users', select 'LoginLockout' from the add
list.  Give it an id and title, and push the add button.

3. Enable the 'Authentication', 'Challenge' and the 'Update Credentials'
plugin interfaces in the after-add screen.

4. Rearrange the order of your 'Challenge plugins' so that the
'LoginLockout' plugin is at the top.

5. Repeat the above for your root PAS but as a plugin to

	-  Anonymoususerfactory

	-  Update Credentials

	and ensure LoginLockout is the first Anonymoususerfactory

Steps 2 through 5 below will be done for you by the Plone installer.

That's it! Test it out.



Implementation
--------------

If the root anonymoususerfactory plugin is activated following an
authentication plugin activation then this is an unsuccesful login
attempt. If the password was different from the last unsuccessful
attempt then we incriment a counter in data stored persistently
in the root plugin.

If the instance plugin tries to authenticate a user that has been
marked has having too many attempts then Unauthorised will be raised.
This will activate the challenge plugin which will display a locked
out message instead of another login form.

updateCredentials is called when the login was successful and in this
case we reset the unsuccessful login count.


Copyright, License, Author
--------------------------

Copyright (c) 2007, PretaWeb, Australia,
 and the respective authors. All rights reserved.

Author: Dylan Jay <software@pretaweb.com>

License BSD-ish, see LICENSE.txt


Credits
-------

Thanks to Daniel Nouri and BlueDynamics for their
NoDuplicateLogin which served as the base for this.
