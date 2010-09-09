#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from rapidsms.contrib.locations.models import Location
import utils
from logistics.models import Facility

class Country(Location):
    name = models.CharField(max_length=200, blank=True, null=True)
    slug = models.CharField(max_length=100, blank=True, null=True)
    class Meta:
        verbose_name_plural = "countries"

    def __unicode__(self):
        return self.name

class Province(Location):
    name = models.CharField(max_length=200, blank=True, null=True)
    slug = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return self.name

    @property
    def country(self):
        if self.parent is not None:
            if self.parent.name is not None:
                return self.parent.name
        return ""

class District(Location):
    name = models.CharField(max_length=500, blank=True, null=True)
    slug = models.CharField(max_length=100, blank=True, null=True)
    code = models.PositiveIntegerField(max_length=20, blank=True, null=True)

    def __unicode__(self):
        return self.name

    @property
    def province(self):
        if self.parent is not None:
            if self.parent.name is not None:
                return self.parent.name
        return ""

class School(Location):
    LEVEL_CHOICES = (
        ('P', 'primary'),
        ('S', 'secondary'),
        ('U', 'unknown'),
    )
    name = models.CharField(max_length=200, blank=True, null=True)
    slug = models.CharField(max_length=100, blank=True, null=True)
    code = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    km_to_DEO = models.CharField(max_length=160, blank=True, null=True)
    code = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    satellite_number = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    total_enrollment = models.PositiveIntegerField(max_length=20, blank=True, null=True)
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='U')
    form_number = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def as_html(self):
        return "%s (%s)" % (self.name, self.full_code)

    def active_shipment(self):
        facility = Facility.objects.get(location_id=self.pk)
        return Facility.get_active_shipment(facility)

    @property
    def css_class(self):
        if self.active_shipment() is not None:
            shipment = self.active_shipment()
            if shipment.status == 'P':
                return "bubble green"
            if shipment.status == 'T':
                return "bubble yellow"
            if shipment.status == 'D':
                return "bubble blue"
        return "bubble"

    @property
    def direction(self):
        return self.Direction.CENTER

    
    @property
    def district(self):
        if self.parent is not None:
            if self.parent.name is not None:
                return self.parent.name
        return ""

    @property
    def province(self):
        if self.parent.name is not None:
            if self.parent.parent is not None:
                if self.parent.parent.name is not None:
                    return self.parent.parent.name
        return ""

    @property
    def full_code(self):
        code = self.code if self.code is not None else ""
        sat_num = self.satellite_number if self.satellite_number is not None else ""
        return "%s" % (str(code) + str(sat_num))

    def _contacts(self):
        return self.schoolcontact.all()

    @property
    def contact(self):
        contacts = self._contacts()
        if contacts.count() == 1:
            return contacts[0]
        if contacts.count() == 0:
            return ""
        if contacts.count() > 0:
            return contacts.values_list('name', flat=True)

    @property
    def contact_phone(self):
        contacts = self._contacts()
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
        contacts = self._contacts()
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
    def closest_by_spelling(klass, search_string, n=100):
        d = []

        for obj in klass.objects.all():
            args = [str(obj.name).upper(), search_string.upper()]

            args_dists = utils.calc_dists(*args)

            # use the shortest of these distances
            d.append((search_string, obj,\
                args_dists[0], args_dists[1],\
                args_dists[2]))

        return utils.closest_matches(d, n)
