#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import csv
import datetime

from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.contrib.contenttypes.models import ContentType

from .models import Province
from .models import District
from .models import School
from .models import Confirmation

def index(req):
    return render_to_response("edusupply/index.html",\
        context_instance=RequestContext(req))

def invalids(req):
    return render_to_response("edusupply/invalid.html",\
        {"invalid_confs": Confirmation.objects.filter(valid=False)}, context_instance=RequestContext(req))

def province_dict(province_pk):
    ''' Return a dict with key 'province' and the value is a dict
        containing the province object and all of its districts. '''
    province = get_object_or_404(Province, pk=province_pk)
    districts = District.objects.filter(parent_type=ContentType.objects.get(name="province"),\
        parent_id=province.pk)
    return {"province" : {province : districts}}

def district_dict(district_pk):
    ''' Return a dict with key 'district' and the value is a dict
        containing the district object and all of its schools. '''
    district = get_object_or_404(District, pk=district_pk)
    schools = School.objects.filter(parent_type=ContentType.objects.get(name="district"),\
        parent_id=district.pk)
    return {"district" : {district : schools}}

def detail(req, province_pk, district_pk=None):
    if district_pk is not None:
        dict = district_dict(district_pk)
        district = get_object_or_404(District, pk=district_pk)
        status_list = district.status_as_list
    else:
        dict = province_dict(province_pk)
        province = get_object_or_404(Province, pk=province_pk)
        districts = District.objects.filter(parent_type=ContentType.objects.get(name="province"),\
            parent_id=province.pk)
        prov_stats = list()
        for d in districts:
            prov_stats.extend(d.status_as_list)
        status_list = prov_stats

    stats =  [
        {
            "caption": "Total schools",
            "value":   len(status_list)
        },
        {
            "caption": "Total pending shipments",
            "value":   status_list.count('0')
        },
        {
            "caption": "Total good condition",
            "value":   status_list.count('1')
        },
        {
            "caption": "Total damaged condition",
            "value":   status_list.count('-2')
        },
        {
            "caption": "Total delivered to alternate location",
            "value":   status_list.count('-3')
        },
        {
            "caption": "Total with incomplete cargo",
            "value":   status_list.count('-4')
        }
    ]
    dict.update({'stats':stats})
    return render_to_response("edusupply/details.html", dict,\
        context_instance=RequestContext(req))

def csv_export(req, province_pk=None, district_pk=None):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')

    dist_dict = None
    prov_dict = None
    if district_pk is not None:
        dict = district_dict(district_pk)
        dist_dict = dict['district'] 
    else:
        dict = province_dict(province_pk)
        prov_dict = dict['province']

    writer = csv.writer(response)
    # column labels
    writer.writerow(['province', 'district', 'school name', 'school code',\
        'headmaster', 'phone', 'status'])

    def write_district(dist_dict):
        district = dist_dict.keys().pop()
        for school_list in dist_dict.itervalues():
            for school in school_list:
                row = [district.province, district.name, school.name, school.code,\
                    school.contact, school.contact_phone, school.status_for_detail]
                writer.writerow(row)

    if dist_dict is not None:
        # export a district
        write_district(dist_dict)
        label = dist_dict.keys().pop().name + "-district"

    else:
        # export all of the districts in a province
        for district_list in prov_dict.itervalues():
            for district in district_list:
                write_district(district_dict(district.pk)['district'])
        label = prov_dict.keys().pop().name + "-province"

    filename = "%s-%s" % (datetime.datetime.today().date().isoformat(), label)
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % (filename)
    return response
