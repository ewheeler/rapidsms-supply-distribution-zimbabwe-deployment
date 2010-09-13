#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.conf.urls.defaults import *
import views as views

urlpatterns = patterns('',
    url(r'^$', views.index),
    url(r'^province/(?P<province_pk>\d+)$', views.detail,
        name="view-province"),
    url(r'^province/(?P<province_pk>\d+)/district/(?P<district_pk>\d+)$',
        views.detail,
        name="view-district"),

)
