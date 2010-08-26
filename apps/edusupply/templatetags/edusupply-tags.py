#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime, timedelta

from django import template
register = template.Library()
from django.db.models import Avg
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from logistics.models import *

@register.inclusion_tag("edusupply/partials/stats.html")
def stats():
    return { "stats": [
        {
            "caption": "Total Shipments",
            "value":   Shipment.objects.count()
        },
        {
            "caption": "Total Planned Shipments",
            "value":   Shipment.objects.filter(status='P').count()
        },
        {
            "caption": "Total Shipments In-transit",
            "value":   Shipment.objects.filter(status='T').count()
        },
        {
            "caption": "Total Shipments Delivered",
            "value":   Shipment.objects.filter(status='D').count()
        },
        {
            "caption": "Total Shipments with damaged cargo",
            "value":   Cargo.objects.filter(condition='D').count()
        },
        {
            "caption": "Total Shipments Delivered to alternate location",
            "value":   Cargo.objects.filter(condition='L').count()
        }
    ]}

def fake_progress():
    return {
        "days" : range(11),
        "total_children" : 1200,
        "active_healthworkers" : 20,
        "total_surveys": 500,
        "total_valids": 300,
        "total_goods": 200,
        "total_suspects": 100,
    }

@register.inclusion_tag("edusupply/partials/progress.html")
def progress():
    def unique_list(seq):
        set = {}
        map(set.__setitem__, seq, [])
        return set.keys()
    try:
        campaign = Campaign.objects.get(begin_date__lte=datetime.datetime.now().date(),\
            end_date__gte=datetime.datetime.now().date())

    except ObjectDoesNotExist, MultipleObjectsReturned:
        campaign = Campaign.objects.filter(end_date__lte=datetime.datetime.now()\
                    .date()).order_by('begin_date')[0]
    start = campaign.begin_date
    end = campaign.end_date
    days = []
    # TODO refactor all of this!!!
    for d in range(0, (end - start).days):
        date = start + datetime.timedelta(d)
        
        ass_args = {
            "date__year":  date.year,
            "date__month": date.month,
            "date__day":   date.day
        }
        
        data = {
            "number": d+1,
            "date": date,
            "in_future": date > datetime.datetime.now().date()
        }
        
        if not data["in_future"]:
            shipments_today = Shipment.objects.filter(actual_delivery_time__year=date.\
                    year, actual_delivery_time__month=date.month, actual_delivery_time__day=\
                    date.day)
            unique_shipments_today = unique_list(shipments_today)

            delivered_shipments_with_damaged_cargo = []
            delivered_shipments_to_alt_loc = []

            for shipment in shipments_today:
                for cargo in shipment.cargos.all():
                    if cargo.condition == 'D':
                        delivered_shipments_with_damaged_cargo.append(cargo)
                    if cargo.condition == 'L':
                        delivered_shipments_to_alt_loc.append(cargo)
                        
            data.update({
                "planned": Shipment.objects.filter(status='P').count(),
                "in_transit": Shipment.objects.filter(status='T').count(),
                "delivered": shipments_today.filter(status='D').count(),
                "damaged": len(delivered_shipments_with_damaged_cargo),
                "alternate_loc": len(delivered_shipments_to_alt_loc),
            })
        
            data.update({
                "damaged_perc":    int((float(data["damaged"])    / float(data["delivered"]))    * 100.0) if (data["damaged"]    > 0) else 0,
                "alt_loc_perc":    int((float(data["alternate_loc"])    / float(data["delivered"]))    * 100.0) if (data["alternate_loc"]    > 0) else 0,
            })
        days.append(data)
    return {
        "days" : days,
        "total_planned" : Shipment.objects.filter(status='P').count(),
        "total_in_transit" : Shipment.objects.filter(status='T').count(),
        "total_delivered" : Shipment.objects.filter(status='D').count(),
        "total_damaged": Cargo.objects.filter(condition='D').count(),
        "total_alt_loc": Cargo.objects.filter(condition='L').count()
    }
