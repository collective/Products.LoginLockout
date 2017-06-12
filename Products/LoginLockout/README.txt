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

vLoginLockout can be used as a Plone plugin or with zope and PAS alone.
First we'll show you how it works with Plone.


To Install
----------

Install into Plone via Add/Remove Products 

To Use
------

First login as manager::

Now we'll open up a new browser and attempt to login::

    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> 'Login failed' in anon_browser.contents
    False
    >>> print anon_browser.contents
    <BLANKLINE>
    ...You are now logged in...


Let's try again with another password::

    >>> anon_browser.open(portal.absolute_url()+'/logout')
    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = 'notpassword'
    >>> anon_browser.getControl('Log in').click()
    >>> print anon_browser.contents
    <BLANKLINE>
    ...Login failed...


this incorrect attempt  will show up in the log::


We've installed a Control panel to monitor the login attempts

    >>> admin_browser.open(portal.absolute_url())
    >>> admin_browser.getLink('Site Setup').click()

    >>> admin_browser.getLink('LoginLockout').click()
    >>> print admin_browser.contents
    <html>
    ...
    ...<td>user</td><td>2</td>...



If we try twice more we will be locked out::

    >>> anon_browser.open(portal.absolute_url()+'/logout')
    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = 'notpassword2'
    >>> anon_browser.getControl('Log in').click()
    >>> 'Login failed' in  anon_browser.contents
    True
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = 'notpassword3'
    >>> anon_browser.getControl('Log in').click()
    >>> 'Login failed' in  anon_browser.contents
    True

#   >>> print anon_browser.contents
#   <html>
#   ...
#   You have been locked out. Please contact the system administrator


Now even the correct password won't work::

    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> 'This account has now been locked for security purposes.' in  anon_browser.contents
    True


The administrator can reset this persons account::

    >>> admin_browser.getLink('Site Setup').click()
    >>> admin_browser.getLink('LoginLockout').click()
    >>> print admin_browser.contents
    user attempts 4
    >>> admin_browser.getControl('user').click()
    >>> admin_browser.getControl('reset accounts').click()
    >>> print admin_browser.contents
    User accounts reset...

and now they can log in again::

    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> print anon_browser.contents
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

Author: Dylan Jay <software pretaweb com>

License BSD-ish, see LICENSE.txt


Credits
-------
Dylan Jay, original code.

Kees HinK for the Plone configlet and installer

Thanks to Daniel Nouri and BlueDynamics for their
NoDuplicateLogin which served as the base for this.
