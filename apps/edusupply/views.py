#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.contrib.contenttypes.models import ContentType

from .models import Province
from .models import District
from .models import School

def index(req):
    return render_to_response("edusupply/index.html",\
        context_instance=RequestContext(req))

def detail(req, province_pk, district_pk=None):
    print province_pk
    print district_pk
    province = get_object_or_404(Province, pk=province_pk)
    print province
    if district_pk is not None:
        district = get_object_or_404(District, pk=district_pk)
        schools = School.objects.filter(parent_type=ContentType.objects.get(name="district"),\
            parent_id=district.pk)
        dict = {"district" : {district : schools}}
    else:
        districts = District.objects.filter(parent_type=ContentType.objects.get(name="province"),\
            parent_id=province.pk)
        dict = {"province" : {province : districts}}

    print dict
    return render_to_response("edusupply/details.html", dict,\
        context_instance=RequestContext(req))
