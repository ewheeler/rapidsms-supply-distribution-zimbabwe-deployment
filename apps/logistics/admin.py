#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.contrib import admin
from .models import *

class CommodityAdmin(admin.ModelAdmin):
    list_display = ("name", "aliases", "unit", "volume", "weight")

class CargoAdmin(admin.ModelAdmin):
    list_filter = ("commodity", )

class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("cargos_str", "origin", "destination", "status", "dispatch_time", "actual_delivery_time")
    list_filter = ("status",)
    date_hierarchy = "dispatch_time"

class ShipmentSightingAdmin(admin.ModelAdmin):
    list_display = ("observed_cargo", "facility", "seen_by", "updated")
    date_hierarchy = "updated"

class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "begin_date", "end_date", "facility", "location", "commodities_str")
    date_hierarchy = "begin_date"

admin.site.register(Commodity, CommodityAdmin)
admin.site.register(Cargo, CargoAdmin)
admin.site.register(Shipment, ShipmentAdmin)
admin.site.register(ShipmentRoute)
admin.site.register(ShipmentSighting, ShipmentSightingAdmin)
admin.site.register(Campaign, CampaignAdmin)
