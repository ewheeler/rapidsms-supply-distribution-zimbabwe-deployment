#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from rapidsms.contrib.locations.models import Location

import utils

class HeadmasterOrDEO(models.Model):
    phone = models.CharField(max_length=160, blank=True, null=True)
    alternate_phone = models.CharField(max_length=160, blank=True, null=True)
    facilities = models.ManyToManyField(Location, related_name='facilitycontact', blank=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def closest_by_name(klass, search_string, n=100):
        d = []

        for obj in klass.objects.all():
            args = [str(obj.name).upper(), search_string.upper()]
            alt_args = [max(str(obj.name).replace('.', ' ').split()).upper(), search_string.upper()]

            args_dists = utils.calc_dists(*args)
            alt_dists = utils.calc_dists(*alt_args)

            # use the shortest of these distances
            d.append((search_string, obj,\
                min([args_dists[0], alt_dists[0]]),\
                min([args_dists[1], alt_dists[1]]),\
                max([args_dists[2], alt_dists[2]])))

        return utils.closest_matches(d, n)
