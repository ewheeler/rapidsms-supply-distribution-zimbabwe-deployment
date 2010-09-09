#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.contrib import admin
from .models import *

class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "full_code", "district", "province", "contact", "contact_phone", "km_to_DEO")
    search_fields = ("name", "slug", "code", "address", "km_to_DEO")

class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "province")
    search_fields = ("name", "slug", "code")

class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    search_fields = ("name", "slug")

admin.site.register(School, SchoolAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(Province, ProvinceAdmin)
admin.site.register(Country)
