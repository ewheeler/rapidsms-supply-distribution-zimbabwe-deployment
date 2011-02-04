#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from django.contrib.contenttypes.models import ContentType
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.messagelog.models import Message
import utils
from logistics.models import Facility
from logistics.models import Cargo

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

    # TODO this is silly. maybe district.status should contain
    # a pickled list object instead of just text?
    status = models.CharField(max_length=500, blank=True, null=True)

    def __unicode__(self):
        return self.name

    @property
    def deo(self):
        contacts = self.districtcontact.all()
        if contacts.count() == 1:
            return contacts[0]
        if contacts.count() == 0:
            return ""
        if contacts.count() > 0:
            return contacts[0]

    @property
    def province(self):
        if self.parent is not None:
            if self.parent.name is not None:
                return self.parent.name
        return ""

    @property
    def status_for_spark(self):
        ''' Returns self.status sans brackets. Otherwise the first
            and last ticks of the sparkline will always display 0. '''
        # TODO this is silly. maybe district.status should contain
        # a pickled list object instead of just text?
        return str(self.status).strip('[]')

    @property
    def status_as_list(self):
        ''' Returns self.status as a list of strings
            instead of a string. '''
        # TODO this is silly. maybe district.status should contain
        # a pickled list object instead of just text?

        # d.status returns a unicode string :(
        # so strip the brackets and split on commas to
        # transform it into a list of unicode items
        as_list = self.status.strip('[]').split(',')
        # strip any leading whitespace from each list element,
        # cast as strings, and add to the aggregate list
        return [str(i.strip()) for i in as_list]

    @property
    def spark(self):
        ''' Refresh and return a list of integers describing delivery status of
            all of the schools in the district for use with
            jquery.sparklines charts. This is very slow and expensive.
            Use the status_for_spark property in templates -- this is only
            for generating or refreshing the district level status list.'''
        try:
            schools = School.objects.filter(parent_type=ContentType.objects.get(name="district"),\
                parent_id=self.pk)
        except Exception, e:
            print 'BANG spark'
            print e
        tristate = []
        for school in schools:
            try:
                if school.active_shipment() is not None:
                    shipment = school.active_shipment()
                    # no status for pending and in-transit shipments
                    if shipment.status == 'P':
                        school.status = 0
                    if shipment.status == 'T':
                        school.status = 0
                    if shipment.status == 'D':
                        try:
                            cargo = shipment.cargos.all()[0]
                            if cargo.condition == 'G':
                                school.status = 1
                            if cargo.condition == 'D':
                                school.status = -2
                            if cargo.condition == 'L':
                                school.status = -3
                            if cargo.condition == 'I':
                                school.status = -4
                        except Exception, e:
                            print 'BANG spark cargo'
                            print e
                    tristate.append(int(school.status))
            except Exception, e:
                print 'BANG spark shipment'
                print e
                tristate.append(int(school.status))
            school.save()
        self.status = tristate
        self.save()
        return tristate

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

    status = models.IntegerField(max_length=8, blank=True, null=True, default=0)

    def __unicode__(self):
        return self.name

    def as_html(self):
        ''' Return label for map pins.
            This can include html. '''
        return "%s" % (self.name)

    def active_shipment(self):
        ''' Return a shipment destined to this school's
            corresponding Facility object. '''
        facility = self.facility()
        return Facility.get_active_shipment(facility)

    def facility(self):
        ''' Return corresponding Facility object '''
        facility = Facility.objects.get(location_type=ContentType.objects.get(name='school'),\
            location_id=self.pk)
        return facility

    @property
    def status_for_detail(self):
        ''' Returns a textual status for the school.
            This is displayed in table on the school detail partial template. '''
        stat = self.status
        if stat == 0:
            return 'Pending'
        else:
            # map the status-for-sparkline onto cargo's condition tuple of tuples
            map = {1:0, -2:1, -3:2, -4:3}
            return Cargo.CONDITION_CHOICES[map[stat]][1]

    @property
    def css_table_class(self):
        ''' Returns a simple status for the school.
            This is used as a css class on the detail
            partial so that rows are colored red or green. '''
        if self.status == 0:
            return 'pending'
        elif self.status == 1:
            return 'good'
        else:
            return 'warning'

    @property
    def css_class(self):
        ''' Returns a css class for map pin display. '''
        stat = self.status
        if stat > 0:
            return "bubble green"
        elif stat < 0:
            return "bubble red"
        else:
            return "bubble"

    @property
    def direction(self):
        ''' Returns a config option for map pin dispay. '''
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
        ''' Returns school code as a string. '''
        code = self.code if self.code is not None else ""
        return "%s" % (str(code))

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
        if self.active_shipment().delivery_sighting != "":
            seen_by = self.active_shipment().delivery_sighting.seen_by
            if seen_by is not None:
                return seen_by
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

class Confirmation(models.Model):
    CONDITION_CHOICES = (
        ('G', 'Good'),
        ('D', 'Damaged'),
        ('L', 'Alternate delivery location'),
        ('I', 'Incomplete'),
    )
    valid = models.BooleanField(default=False)
    corrected = models.NullBooleanField(blank=True, null=True)
    duplicate = models.NullBooleanField(blank=True, null=True)
    replied_to = models.DateTimeField(blank=True, null=True)
    message = models.ForeignKey(Message)
    school = models.ForeignKey(School, blank=True, null=True)
    possible_schools = models.CharField(max_length=500, blank=True, null=True)
    code = models.CharField(max_length=8, blank=True, null=True)
    condition = models.CharField(max_length=3, choices=CONDITION_CHOICES, blank=True, null=True)
    token_list = models.CharField(max_length=500, blank=True, null=True)

    @property
    def get_possible_schools(self):
        p_schools = []
        if self.possible_schools is not None:
            for ps in self.possible_schools:
                s = School.objects.get(pk=ps)
                if s is not None:
                    p_schools.append(s)
        return p_schools
