#!/usr/bin/env python
# vim: et ts=4 sw=4


# inherit everything from rapidsms, as default
# (this is optional. you can provide your own.)
from rapidsms.djangoproject.settings import *


# then add your django settings:

DATABASE_ENGINE = "sqlite3"
DATABASE_NAME = "db.sqlite3"

INSTALLED_APPS = (
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.auth",

    "rapidsms",
    "rapidsms.contrib.ajax", 
    "rapidsms.contrib.httptester", 
    "rapidsms.contrib.handlers", 
    "rapidsms.contrib.locations",

    # enable the django admin using a little shim app (which includes
    # the required urlpatterns)
    "rapidsms.contrib.djangoadmin",
    "django.contrib.admin",
    
    "apps.edusupply",
    "apps.logistics",
    
    "rapidsms.contrib.default",
)

INSTALLED_BACKENDS = {
    #"AT&T": {
    #    "ENGINE": "rapidsms.backends.gsm",
    #    "PORT": "/dev/ttyUSB0"
    #},
    #"Verizon": {
    #    "ENGINE": "rapidsms.backends.gsm,
    #    "PORT": "/dev/ttyUSB1"
    #},
    "message_tester" : {"ENGINE": "rapidsms.backends.bucket" } 
}

# after login, django redirects to this URL
# rather than the default 'accounts/profile'
LOGIN_REDIRECT_URL='/'
