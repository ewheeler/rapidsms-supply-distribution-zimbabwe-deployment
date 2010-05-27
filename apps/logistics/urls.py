#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.conf.urls.defaults import *

import views as v

urlpatterns = patterns('',
    
    # mini dashboard for this app
    url(r'^logistics/?$',
        v.index),

#    url(r'^logistics/csv/reports?$', 
#        v.csv_reports),
 
)
