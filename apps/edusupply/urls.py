#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.conf.urls.defaults import *

import views as v

urlpatterns = patterns('',
    
    # mini dashboard for this app
    url(r'^edusupply/?$',
        v.index),

#    url(r'^edusupply/csv/reports?$', 
#        v.csv_reports),
 
)
