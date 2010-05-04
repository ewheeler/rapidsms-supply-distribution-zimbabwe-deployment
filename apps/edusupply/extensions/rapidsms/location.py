#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models

class School(models.Model):
    address = models.CharField(max_length=500, blank=True, null=True)
    km_to_DEO = models.Charfield(max_length=160, blank=True, null=True)
    code = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    satellite_id = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    
    class Meta:
        abstract = True
