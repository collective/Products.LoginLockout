LoginLockout
============

.. image:: https://github.com/collective/Products.LoginLockout/workflows/CI/badge.svg
  :target: https://github.com/collective/Products.LoginLockout/actions

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

- (optional) Plone 4.1.x-5.2.x

.. image:: http://github-actions.40ants.com/collective/Products.LoginLockout/matrix.svg
   :target: https://github.com/collective/Products.LoginLockout


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

You can use this plugin with Zope without Plone, or with Plone. When using it with Plone you will configure it via the
Plone registry (plone 5+) or via portal_properties if plone 4.

Go to the Plone Control Panel -> LoginLockout Settings , there you can changes these defaults:

    >>> admin_browser = make_admin_browser('/')
    >>> admin_browser.getLink('Site Setup').click()
    >>> admin_browser.getLink('LoginLockout').click()
    >>> admin_browser.getLink('Lockout Settings').click()

- allowed incorrect attempts: 3
- reset period: 24 hours
- whitelist_ips: [] # any origin IP is allowed
- Fake Client IP: false
    
    >>> admin_browser.getControl("Max Attempts").value
    '3'
    >>> admin_browser.getControl("Reset Period (hours)").value
    '24.0'
    >>> admin_browser.getControl('Lock logins to IP Ranges').value
    ''
    >>> admin_browser.getControl('Fake Client IP').selected
    False


Let's ensure that the settings actually change

    >>> admin_browser.getControl('Fake Client IP').selected = True
    >>> get_loginlockout_settings().fake_client_ip
    False
    >>> admin_browser.getControl('Save').click()
    >>> 'Changes saved.' in admin_browser.contents
    True
    >>> get_loginlockout_settings().fake_client_ip
    True



Details
-------

LoginLockout can be used as a Plone plugin or with zope and PAS alone.
First we'll show you how it works with Plone.


To Install
----------

Install into Plone via Add/Remove Products. If you are installing into zope without
plone then you will need to follow these manual install steps.

This will install and activate a two PAS plugins.

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

    -  Challenge

   and ensure LoginLockout is the first Anonymoususerfactory and Challenge plugin

Steps 2 through 5 below will be done for you by the Plone installer.

That's it! Test it out.


Plone LoginLockout PAS Plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's very important the plugin is the *first* Challange plugin in the activated plugins list.
This ensures we redirect a person attempting to make a login into a locked account to a special page.

   >>> plone_pas = portal.acl_users.plugins
   >>> IChallengePlugin = plone_pas._getInterfaceFromName('IChallengePlugin')
   >>> plone_pas.listPlugins(IChallengePlugin)
   [('login_lockout_plugin', <LoginLockout at /plone/acl_users/login_lockout_plugin>)...]


In addition it is installed as a IAuthenticationPlugin. This both collects the username and login and
will prevent a login should it be locked.

   >>> IAuthenticationPlugin = plone_pas._getInterfaceFromName('IAuthenticationPlugin')
   >>> 'login_lockout_plugin' in [p[0] for p in plone_pas.listPlugins(IAuthenticationPlugin)]
   True

and a ICredentialsUpdatePlugin. This records when a login was successful to reset attempt data.


   >>> ICredentialsUpdatePlugin = plone_pas._getInterfaceFromName('ICredentialsUpdatePlugin')
   >>> 'login_lockout_plugin' in [p[0] for p in plone_pas.listPlugins(ICredentialsUpdatePlugin)]
   True


Root Zope LoginLockout PAS Plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It will also install a plugin at the root of the zope instance.

It's important this is also the *first* IAnonymousUserFactoryPlugin. On a normal Zope instance it will be the only one.
This ensures it collects data on unsuccessful attempted logins.

   >>> root_pas = portal.getPhysicalRoot().acl_users.plugins
   >>> IAnonymousUserFactoryPlugin = plone_pas._getInterfaceFromName('IAnonymousUserFactoryPlugin')
   >>> root_pas.listPlugins(IAnonymousUserFactoryPlugin)
   [('login_lockout_plugin', <LoginLockout at /acl_users/login_lockout_plugin>)]

It is also installed as a IChallengePlugin.

   >>> 'login_lockout_plugin' in [p[0] for p in root_pas.listPlugins(IChallengePlugin)]
   True


Lockout on incorrect password attempts
--------------------------------------

First login as manager::

Now we'll open up a new browser and attempt to login::

    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> 'Login failed' in anon_browser.contents
    False
    >>> print(anon_browser.contents)
    <BLANKLINE>
    ...You are now logged in...

    >>> anon_browser.open(portal.absolute_url()+'/logout')


Let's try again with another password::

    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = 'notpassword'
    >>> anon_browser.getControl('Log in').click()
    >>> print(anon_browser.contents)
    <BLANKLINE>
    ...Login failed...


this incorrect attempt  will show up in the log::


We've installed a Control panel to monitor the login attempts

    >>> admin_browser = make_admin_browser('/loginlockout_settings')
    >>> print(admin_browser.contents)
    <BLANKLINE>
    ...<td>test-user</td>...
    ...<td>1</td>...



If we try twice more we will be locked out::

    >>> anon_browser = make_anon_browser('/login_form')
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

#   >>> print(anon_browser.contents)
#   <html>
    <BLANKLINE>
    ...This account has now been locked for security purposes...


Now even the correct password won't work::

    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    Traceback (most recent call last):
    ...
    Unauthorized: Unauthorized()


The administrator can reset this persons account::

    >>> admin_browser = make_admin_browser('/loginlockout_settings')
    >>> print(admin_browser.contents)
    <BLANKLINE>
    ...<td>test-user</td>...
    ...<td>3</td>...
    >>> admin_browser.getControl(name='reset_nonploneusers:list').value = ['test-user']
    >>> admin_browser.getControl('Reset selected accounts').click()
    >>> print(admin_browser.contents)
    <BLANKLINE>
    ...Accounts were reset for these login names: test-user...

and now they can log in again::

    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> print(anon_browser.contents)
    <BLANKLINE>
    ...You are now logged in...

IP Lockdown
-----------

You can optionally ensure logins are only possible for certain IP address ranges.

By default IP Locking is disabled.

NOTE: If you are using Zope behind a proxy then you must enable X-Forward-For headers on
each proxy otherwise this plugin will incorrectly use REMOTE_ADDR which will be a local IP.

To enable this go into the ZMI and enter the ranges in the whitelist_ips property

    >>> config_property( whitelist_ips = u'10.1.1.1' )

If there are proxies infront of zope you will have to ensure they set the ```X-Forwarded-For``` header.
Note only the first forwarded IP will be used.

    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.addHeader('X-Forwarded-For', '10.1.1.1, 192.168.1.1')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> print(anon_browser.contents)
    <BLANKLINE>
    ...You are now logged in...

    >>> anon_browser.open(portal.absolute_url()+'/logout')

If not from a valid IP then the login will fail

    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.addHeader('X-Forwarded-For', '2.2.2.2')

    >>> anon_browser.open(portal.absolute_url()+'/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    Traceback (most recent call last):
    ...
    Unauthorized: Unauthorized()


Basic Auth will works with the right IP

    >>> anon_browser = make_anon_browser()
    >>> anon_browser.addHeader('Authorization', 'Basic %s:%s' % (user_id,user_password))
    >>> anon_browser.addHeader('X-Forwarded-For', '10.1.1.1')

    >>> anon_browser.open(portal.absolute_url())
    >>> anon_browser.getLink('Log out')
    <Link text='Log out'...>


and basic auth fails with the wrong IP

    >>> anon_browser = make_anon_browser()
    >>> anon_browser.addHeader('Authorization', 'Basic %s:%s' % (user_id,user_password))
    >>> anon_browser.addHeader('X-Forwarded-For', '2.2.2.2')

    >>> anon_browser.open(portal.absolute_url())
    Traceback (most recent call last):
    ...
    Unauthorized: Unauthorized()


We can still use a root login at the root

    >>> anon_browser = make_anon_browser()
    >>> anon_browser.addHeader('Authorization', 'Basic %s:%s' % (base_id, base_password))
    >>> anon_browser.addHeader('X-Forwarded-For', '2.2.2.2')

Manage would raise an Unauthorised Exception if the login failed
    >>> anon_browser.open(portal.absolute_url()+'/../manage')


but not in the plone site

    >>> anon_browser.open(portal.absolute_url())
    Traceback (most recent call last):
    ...
    Unauthorized: Unauthorized()


You can also set IP ranges e.g.

    >>> config_property( whitelist_ips = u"""10.1.1.1
    ... 10.1.0.0/16 # range 1
    ... 2.2.0.0/16 # range 2
    ... """)

    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.addHeader('X-Forwarded-For', '2.2.2.2')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()
    >>> print(anon_browser.contents)
    <BLANKLINE>
    ...You are now logged in...

    >>> anon_browser.open(portal.absolute_url()+'/logout')

You can also set a env variable LOGINLOCKOUT_IP_WHITELIST which is merged with the config.
This allows those with filesystem access a way to get in if they have set their config wrong.
It also allows a set of IP ranges to be set for any site in a Plone multisite setup as long
as the site has loginlockout installed.


    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.getLink('Log in')
    <Link text='Log in'...

    >>> import os; os.environ["LOGINLOCKOUT_IP_WHITELIST"] = "3.3.3.3"

    >>> anon_browser.addHeader('Authorization', 'Basic %s:%s' % (user_id,user_password))
    >>> anon_browser.addHeader('X-Forwarded-For', '3.3.3.3')

    >>> anon_browser.open(portal.absolute_url())
    >>> anon_browser.getLink('Log out')
    <Link text='Log out'...>


Note that you still have to have the IP lockout config set otherwise logins are allowed from anywhere
even with the env variable set

    >>> config_property( whitelist_ips = u"""
    ... """)
    >>> anon_browser = make_anon_browser()
    >>> anon_browser.addHeader('Authorization', 'Basic %s:%s' % (user_id,user_password))
    >>> anon_browser.addHeader('X-Forwarded-For', '4.4.4.4')

    >>> anon_browser.open(portal.absolute_url())
    >>> anon_browser.getLink('Log out')
    <Link text='Log out'...>


    >>> del os.environ["LOGINLOCKOUT_IP_WHITELIST"]


If you are unsure of what is being detected as your current Client IP you can see it in
the control panel

    >>> admin_browser = make_admin_browser('/')
    >>> admin_browser.addHeader('X-Forwarded-For', '10.1.1.1, 192.168.1.1')

    >>> admin_browser.getLink('Site Setup').click()
    >>> admin_browser.getLink('LoginLockout').click()
    >>> print(admin_browser.contents)
    <BLANKLINE>
    ...Current detected Client IP: <span>10.1.1.1</span>...


Login History
-------------

It is also possible to view a history of successful logins for a particular user. Note this is the user id rather
than user login and they can be different. User test_user_1_ had 4 successful logins.

    >>> admin_browser = make_admin_browser('/loginlockout_settings')
    >>> admin_browser.getLink('Login history').click()
    >>> admin_browser.getControl('Username pattern').value = 'test_user_1_'
    >>> admin_browser.getControl('Search records').click()
    >>> print(admin_browser.contents)
    <BLANKLINE>
    ...
                        <td valign="top">test_user_1_</td>
                        <td valign="top">
                            <ul>
                                <li>
                                    ...
                                    ()
                                </li>
                                <li>
                                    ...
                                    ()
                                </li>
                                <li>
                                    ...
                                    (10.1.1.1)
                                </li>
                                <li>
                                    ...
                                    (2.2.2.2)
                                </li>
                            </ul>
    ...



Password Reset History
----------------------

When a user changes their password

    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = user_password
    >>> anon_browser.getControl('Log in').click()

    >>> anon_browser.getLink("Preferences").click()
    >>> anon_browser.getLink("Password").click()
    >>> anon_browser.getControl('Current password').value = user_password
    >>> anon_browser.getControl('New password').value = '12345678'
    >>> anon_browser.getControl('Confirm password').value = '12345678'
    >>> anon_browser.getControl('Change Password').click()
    >>> print(anon_browser.contents)
    <...
    ...Password changed... 
    ...

This changed the password
    >>> anon_browser = make_anon_browser('/login_form')
    >>> anon_browser.getControl('Login Name').value = user_id
    >>> anon_browser.getControl('Password').value = '12345678'
    >>> anon_browser.getControl('Log in').click()
    >>> anon_browser.getLink("Preferences").click()

The the administrators can see the password was changed

    >>> admin_browser = make_admin_browser('/loginlockout_settings')
    >>> admin_browser.getLink('History password changes').click()
    >>> print(admin_browser.contents)
    <...
    ...
            <tr class="even">
                <td>test_user_1_</td>
                <td>...</td>
            </tr>
    ...


Implementation
--------------

If the root anonymoususerfactory plugin is activated following an
authentication plugin activation then this is an unsuccesful login
attempt. If the password was different from the last unsuccessful
attempt then we increment a counter in data stored persistently
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

- Move skins to browser views

- get rid of overrides for pw resets. Should be able to do in PAS or using events

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
