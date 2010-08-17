#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from rapidsms.contrib.locations.models import Location
import utils

class Country(Location):
    name = models.CharField(max_length=200, blank=True, null=True)
    slug = models.CharField(max_length=100, blank=True, null=True)
    class Meta:
        verbose_name_plural = "countries"

class Province(Location):
    name = models.CharField(max_length=200, blank=True, null=True)
    slug = models.CharField(max_length=100, blank=True, null=True)

class District(Location):
    name = models.CharField(max_length=200, blank=True, null=True)
    slug = models.CharField(max_length=100, blank=True, null=True)
    code = models.PositiveIntegerField(max_length=20, blank=True, null=True)

class School(Location):
    name = models.CharField(max_length=200, blank=True, null=True)
    slug = models.CharField(max_length=100, blank=True, null=True)
    code = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    km_to_DEO = models.CharField(max_length=160, blank=True, null=True)
    code = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    satellite_number = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    
    @property
    def full_code(self):
        return "%s" % (str(self.code) + str(self.satellite_number))

    @property
    def contact(self):
        contacts = self.facilitycontact.all()
        if contacts.count() == 1:
            return contacts[0]
        if contacts.count() == 0:
            return ""
        if contacts.count() > 0:
            return contacts.values_list('name', flat=True)

    @property
    def contact_phone(self):
        contacts = self.facilitycontact.all()
        if contacts.count() == 1:
            connections = contacts[0].connection_set.all()
            if connections.count() == 1:
                return connections[0]
            if connections.count() > 1:
                return connections.values_list('identity', flat=True)
            if contacts[0].phone is not None:
                return contacts[0].phone
            else:
                return ""
        if contacts.count() == 0:
            return ""
        if contacts.count() > 0:
            return contacts.values_list('phone', flat=True)

    @property
    def contact_alt_phone(self):
        contacts = self.facilitycontact.all()
        if contacts.count() == 1:
            if contacts[0].alternate_phone is not None:
                return contacts[0].alternate_phone
            else:
                return ""
        if contacts.count() == 0:
            return ""
        if contacts.count() > 0:
            return contacts.values_list('alternate_phone', flat=True)

    @classmethod
    def closest_by_code(klass, search_string, n=100):
        d = []

        for obj in klass.objects.all():

            args = [str(obj.code), search_string]
            alt_args = [str(obj.code) + str(obj.satellite_number), search_string]

            args_dists = utils.calc_dists(*args)
            alt_dists = utils.calc_dists(*alt_args)

            # use the shortest of these distances
            d.append((search_string, obj,\
                min([args_dists[0], alt_dists[0]]),\
                min([args_dists[1], alt_dists[1]]),\
                max([args_dists[2], alt_dists[2]])))

        return utils.closest_matches(d, n)


    @classmethod
    def closest_by_name(klass, search_string, n=100):
        d = []

        for obj in klass.objects.all():
            args = [str(obj.name).upper(), search_string.upper()]

            args_dists = utils.calc_dists(*args)

            # use the shortest of these distances
            d.append((search_string, obj,\
                args_dists[0], args_dists[1],\
                args_dists[2]))

        return utils.closest_matches(d, n)
