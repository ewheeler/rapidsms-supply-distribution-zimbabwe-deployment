#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.templatetags.tabs_tags import register_tab
from django.template import RequestContext
from django.shortcuts import render_to_response

from .models import Shipment

def index(req):
    return render_to_response("logistics/index.html",\
        {'shipments': Shipment.objects.all()},\
        context_instance=RequestContext(req))
