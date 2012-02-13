from setuptools import setup, find_packages
import sys, os

version = '0.3.1'

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(name='Products.LoginLockout',
      version=version,
      description="This Pluggable Authentication Service (PAS) plugin will lock a \
                   login after a predetermined number of incorrect attempts. Once \
                   locked, the user will be shown a page that tells them to contact \
                   their administrator to unlock.",
      long_description=(
        read('Products/LoginLockout/README.txt')
        + '\n\n' +
        read('Products/LoginLockout/CHANGES.txt')
        ),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Zope2",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='zope PAS',
      author='Dylan Jay',
      author_email='software@pretaweb.com',
      url='http://plone.org/products/loginlockout',
      license='GPL',
      packages=find_packages(),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          # Products.PluggableAuthService is a dep, but can't be explicit in Plone 3.
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
