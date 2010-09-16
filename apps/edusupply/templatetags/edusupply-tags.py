#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime, timedelta

from django import template
register = template.Library()
from django.db.models import Avg
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.contenttypes.models import ContentType

from logistics.models import *
from edusupply.models import *

@register.inclusion_tag("edusupply/partials/stats.html")
def stats():
    return { "stats": [
        {
            "caption": "Total shipments",
            "value":   Shipment.objects.count()
        },
        {
            "caption": "Total planned shipments",
            "value":   Shipment.objects.filter(status='P').count()
        },
        {
            "caption": "Total shipments delivered",
            "value":   Shipment.objects.filter(status='D').count()
        },
        {
            "caption": "Total shipments with damaged cargo",
            "value":   Cargo.objects.filter(condition='D').count()
        },
        {
            "caption": "Total shipments delivered to alternate location",
            "value":   Cargo.objects.filter(condition='L').count()
        },
        {
            "caption": "Total shipments with incomplete cargo",
            "value":   Cargo.objects.filter(condition='I').count()
        }
    ]}

@register.inclusion_tag("edusupply/partials/charts.html")
def charts():
    provinces = Province.objects.all()
    dict = {}
    for province in provinces:
        try:
            districts = District.objects.filter(parent_type=ContentType.objects.get(name="province"),\
                parent_id=province.pk)
        except Exception, e:
            print e
        dict.update({province: districts})

    return {"provinces": dict }
