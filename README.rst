LoginLockout
============

.. image:: https://api.travis-ci.org/collective/Products.LoginLockout.svg
  :target: https://travis-ci.org/collective/Products.LoginLockout

.. image:: https://coveralls.io/repos/collective/Products.LoginLockout/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/collective/Products.LoginLockout?branch=master

This Pluggable Authentication Service (PAS) plugin will lock a
login after a predetermined number of incorrect attempts. Once
locked, the user will be shown a page that tells them to contact
their administrator to unlock.


Requires:
---------

- PluggableAuthService and its dependencies

- (optional) PlonePAS and its dependencies


Features
--------

- Configurable number of allowed incorrect attempts before lockout
- Account will be usable again after a configurable amount of time
  (the "reset period")
  If the first login attempt after the reset period is invalid, the
  invalid login counter is set to 1.
- The user is presented with a message saying that the account was locked,
  and for how long.
  (It doesn't show remaining time, just the total lockout time.)
- You can restrict users to come from certain IP networks. You don't have to
  use the incorrect login attempts to use this feature.


Configuration
-------------

Go to the ZMI -> portal_properties -> loginlockout_properties,
there you can changes these defaults:

- allowed incorrect attempts: 3
- reset period: 24 hours
- whitelist_ips: [] # any origin IP is allowed


Details
-------

LoginLockout can be used as a Plone plugin or with zope and PAS alone.
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

    >>> anon_browser.open(portal.absolute_url()+'/logout')


Let's try again with another password::

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
    <BLANKLINE>
    ...<td>test-user</td>...
    ...<td>1</td>...



If we try twice more we will be locked out::

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
    <BLANKLINE>
    ...This account has now been locked for security purposes...


Now even the correct password won't work::

    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    Traceback (most recent call last):
    ...
    Unauthorized: Unauthorized()


The administrator can reset this persons account::

    >>> admin_browser.getLink('Site Setup').click()
    >>> admin_browser.getLink('LoginLockout').click()
    >>> print admin_browser.contents
    <BLANKLINE>
    ...<td>test-user</td>...
    ...<td>3</td>...
    >>> admin_browser.getControl(name='reset_nonploneusers:list').value = ['test-user']
    >>> admin_browser.getControl('Reset selected accounts').click()
    >>> print admin_browser.contents
    <BLANKLINE>
    ...<dd>Accounts were reset for these login names: test-user</dd>...

and now they can log in again::

    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> print anon_browser.contents
    <BLANKLINE>
    ...You are now logged in...

IP Lockdown
----------

You can optionally ensure logins are only possible for certain IP address ranges. 

By default IP Locking is disabled.

NOTE: If you are using Zope behind a proxy then you must enable X-Forward-For headers on
each proxy otherwise this plugin will incorrectly use REMOTE_ADDR which will be a local IP.

To enable this go into the ZMI and enter the ranges in the whitelist_ips property

    >>> range = '10.1.1.1'

    >>> admin_browser.open(portal.absolute_url()+'/acl_users/login_lockout_plugin/manage_propertiesForm')
    >>> admin_browser.getControl(name='_whitelist_ips:lines').value = range
    >>> admin_browser.getControl(name='manage_editProperties:method').click()

If there are proxies infront of zope you will have to ensure they set the ```X-Forwarded-For``` header.
Note only the first forwarded IP will be used.

    >>> anon_browser.addHeader('X-Forwarded-For', '10.1.1.1, 192.168.1.1')

    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> print anon_browser.contents
    <BLANKLINE>
    ...You are now logged in...

    >>> anon_browser.open(portal.absolute_url()+'/logout')
    >>> _ = anon_browser.mech_browser.addheaders.pop() # remove X-Forwarded-For header


If not from a valid IP then the login will fail

    >>> anon_browser.addHeader('X-Forwarded-For', '2.2.2.2')

    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    Traceback (most recent call last):
    ...
    Unauthorized: Unauthorized()

    >>> _ = anon_browser.mech_browser.addheaders.pop() # remove X-Forwarded-For header

You can also set IP ranges e.g.

    >>> range = """
    ... 10.1.1.1/24
    ... 2.2.2.2/24
    ... """


    >>> admin_browser.open(portal.absolute_url()+'/acl_users/login_lockout_plugin/manage_propertiesForm')
    >>> admin_browser.getControl(name='_whitelist_ips:lines').value = range
    >>> admin_browser.getControl(name='manage_editProperties:method').click()

    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> print anon_browser.contents
    <BLANKLINE>
    ...You are now logged in...

    >>> anon_browser.open(portal.absolute_url()+'/logout')
    >>> _ = anon_browser.mech_browser.addheaders.pop() # remove X-Forwarded-For header


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


Troubleshooting
---------------

AttributeError: manage_addLoginLockout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If, while running test, you get ``AttributeError: manage_addLoginLockout``,
this is likely due to the fact that the ``initialize()`` method from ``__init__.py``
isn't run during test setup.

To resolve, explicitly call::

    z2.installProduct(portal, 'Products.LoginLockout')


Developing
----------

It's great that you want to help advance this add-on!

To start development:

::

    git clone git@github.com:collective/Products.LoginLockout.git
    cd Products.LoginLockout
    virtualenv .
    ./bin/python bootstrap.py
    ./bin/buildout
    ./bin/test


Please observe the following:

* Only start work when tests are currently passing.
  If not, fix them, or ask someone (*) for help.

* Make your work in a branch and create a pull request for it on github.
  Ask for someone (*) to merge it.

* Please adhere to guidelines: pep8.
  We use plone.recipe.codeanalysis to enforce some of these.

(*) People that might be able to help you out:
    khink, djay, ajung, macagua


TODO
----
Things that could be done on the LoginLockout product:
- optional use of registry. If registry settings found it overrides plugin settings.
  Then modify these settings in a configlet.
  Get rid of portal_properties. loginlockout is supposed to work with or without plone.

- optional path to store attempts db so it can be stored in historyless db.

- perhaps have a short lock or a captcha to prevent rapid attempts instead of a full lockout

- Only restrict certain groups to certain IP networks e.g. administrators. Maybe roles too?


Copyright, License, Author
--------------------------

Copyright (c) 2007, PretaWeb, Australia,
 and the respective authors. All rights reserved.

Author: Dylan Jay <software pretaweb com>

License BSD-ish, see LICENSE.txt


Credits
-------

Dylan Jay, original code.

Contributors:

* Kees Hink
* Andreas Jung
* Leonardo J. Caballero G.
* Wolfgang Thomas
* Peter Uittenbroek
* Ovidiu Miron
* Ludolf Takens
* Maarten Kling

Thanks to Daniel Nouri and BlueDynamics for their
NoDuplicateLogin which served as the base for this.
