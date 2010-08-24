#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models

class ShipmentAdditions(models.Model):
    delivery_group = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    delivered_by = models.CharField(max_length=160, blank=True, null=True)
    dispatched = models.NullBooleanField(default=False)
    delivered = models.NullBooleanField(default=False)
    confirmed = models.NullBooleanField(default=False)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True
