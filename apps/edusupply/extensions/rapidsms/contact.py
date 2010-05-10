#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from rapidsms.contrib.locations.models import Location

class Headmaster(models.Model):
    alternate_phone = models.CharField(max_length=160, blank=True, null=True)
    school = models.ForeignKey(Location, blank=True, null=True, related_name='headmasters')

    class Meta:
        abstract = True
