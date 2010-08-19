#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.shortcuts import render_to_response
from django.template import RequestContext

def index(req):
    return render_to_response("edusupply/index.html",\
        context_instance=RequestContext(req))
