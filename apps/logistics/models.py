#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from rapidsms.models import ExtensibleModelBase
#from rapidsms.models import Contact

class CommodityBase(models.Model):
    ''' Stuff '''
    UNIT_CHOICES = (
        ('PL', 'pallets'),
        ('TM', 'Tons (metric)'),
        ('KG', 'Kilograms'),
        ('BX', 'Boxes'),
        ('TB', 'Tiny boxes'),
        ('BL', 'Bales'),
        ('LT', 'Liters'),
        ('CN', 'Containers'),
        ('DS', 'Doses'),
        ('KT', 'Kits'),
        ('OT', 'Other'),
        ('UK', 'Unknown'),
    )
    name = models.CharField(max_length=160)
    slug = models.CharField(max_length=20, unique=True)
    # List of alternate spellings, abbreviations, etc that can be specified
    # via webui. eg, enter books, book for object where slug=textbooks
    aliases = models.CharField(max_length=160, blank=True, null=True,\
        help_text="List of alternate spellings, abbreviations, etc. Separate each alias with a single comma and no spaces.")

    # unit of commodity for shipping purposes
    unit = models.CharField(max_length=3, choices=UNIT_CHOICES)

    # per unit shipping volume and weight of commodity
    volume = models.CharField(max_length=160, blank=True, null=True)
    weight = models.CharField(max_length=160, blank=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def alias_list(self):
        ''' Returns a list of self.aliases '''
        if self.aliases is not None:
            return self.aliases.split(',')
        else:
            return None

    def has_alias(self, term):
        ''' Checks whether a search term is in a commodity's list
            of aliases. Returns None if commodity has no aliases,
            and True or False otherwise. '''
        if self.aliases is not None:
            alias_list = self.alias_list()
            if term in alias_list:
                return True
            else:
                return False
        else:
            return None

class Commodity(CommodityBase):
    ''' Stuff '''
    __metaclass__ = ExtensibleModelBase

class CargoBase(models.Model):
    commodity = models.ForeignKey(Commodity)
    quantity = models.CharField(max_length=160, blank=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s %s of %s" % (self.quantity or "??", self.commodity.get_unit_display(), self.commodity.slug)

class Cargo(CargoBase):
    ''' An amount of stuff being transported '''
    __metaclass__ = ExtensibleModelBase

class FacilityBase(models.Model):
    ''' Generic relationship to an instance of a subclass of Location '''
    location_type = models.ForeignKey(ContentType)
    location_id = models.PositiveIntegerField()
    location = generic.GenericForeignKey('location_type', 'location_id')

class Facility(FacilityBase):
    ''' A Location where stuff can be stored or seen '''
    __metaclass__ = ExtensibleModelBase

    def __unicode__(self):
        return getattr(self.location, "name")

    class Meta:
        verbose_name_plural = "facilities"

    @classmethod
    def get_active_shipment(klass, destination):
        ''' Returns a single Shipment (not a queryset)
            destined for the supplied facility '''
        # TODO BUGS BELOW! XXX
        active_shipment = Shipment.objects.filter(\
            destination=destination).order_by('created')
        # if there is only one planned or in-transit, return it
        if active_shipment.count() == 1:
            return active_shipment[0]
        # if there are no planned or in-transit,
        # make a new one and return it with in-transit status
        if active_shipment.count() == 0:
            active_shipment = Shipment.objects.create(\
                destination=destination, status='T')
            return active_shipment
        # if there are many active shipments, return the oldest in-transit shipment
        if active_shipment.count() > 1:
            in_transit = active_shipment.filter(status='T').order_by('created')
            if in_transit.count() > 0:
                return in_transit[0]
            return active_shipment[0]

class ShipmentBase(models.Model):
    STATUS_CHOICES = (
        ('P', 'Planned shipment'),
        ('T', 'Shipment in transit'),
        ('D', 'Shipment delivered'),
    )
    status = models.CharField(max_length=3, choices=STATUS_CHOICES)
    cargos = models.ManyToManyField(Cargo)

    origin = models.ForeignKey(Facility, related_name='originshipments', blank=True, null=True)
    destination = models.ForeignKey(Facility, related_name='destinationshipments')

    created = models.DateTimeField(default=datetime.datetime.utcnow)
    modified = models.DateTimeField(default=datetime.datetime.utcnow)

    # datetime when transport begins
    dispatch_time = models.DateTimeField(blank=True, null=True)
    # estimated delivery datetime
    expected_delivery_time = models.DateTimeField(blank=True, null=True)
    # actual datetime of shipment delivery
    # TODO derive from a ShipmentSighting at destination?
    actual_delivery_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        if self.origin is not None:
            return "%s from %s to %s" % (self.cargos_str, self.origin.location.name, self.destination.location.name)
        else:
            return "%s from ?? to %s" % (self.cargos_str, self.destination.location.name)

    @property
    def cargos_str(self):
        cargos_names = []
        for cargo in self.cargos.all():
            if cargo.__unicode__() not in cargos_names:
                cargos_names.append(cargo.__unicode__())
        return "%s" % (", ".join(cargos_names))

    @property
    def delivery_sighting(self):
        for route in self.shipmentroute_set.all():
            for sighting in route.sightings.all():
                if sighting.facility.location_id == self.destination.location_id:
                    return sighting
        return ""

    @classmethod
    def active(cls):
        return cls.objects.exclude(status="D")

class Shipment(ShipmentBase):
    ''' Transport of stuff(s) between two places '''
    __metaclass__ = ExtensibleModelBase

class ShipmentSightingBase(models.Model):
    updated = models.DateTimeField(default=datetime.datetime.utcnow)
    facility = models.ForeignKey(Facility)
    observed_cargo = models.ForeignKey(Cargo, blank=True, null=True)
    #seen_by = models.ForeignKey(Contact, blank=True, null=True)
    @property
    def seen_by(self):
        return ''

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s seen at %s" % (self.observed_cargo, self.facility.location.name)

class ShipmentSighting(ShipmentSightingBase):
    ''' Location where a person has seen stuff during its shipment '''
    __metaclass__ = ExtensibleModelBase

class ShipmentRouteBase(models.Model):
    shipment = models.ForeignKey(Shipment)
    sightings = models.ManyToManyField(ShipmentSighting)

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s sightings of %s" % (self.sightings.count(), self.shipment)

class ShipmentRoute(ShipmentRouteBase):
    ''' Collection of locations where the stuff has been seen during shipment '''
    __metaclass__ = ExtensibleModelBase

class CampaignBase(models.Model):
    begin_date = models.DateField(blank=True,null=True)
    end_date = models.DateField(blank=True,null=True)
    facility = models.ForeignKey(Facility, blank=True, null=True, help_text="Optional top-level facility or campaign area.")
    location = models.CharField(max_length=160,blank=True,null=True, help_text="Optional location notes.")
    name = models.CharField(max_length=160,blank=True,null=True, help_text="Title of campaign, e.g., Textbooks for primary schools")
    description = models.CharField(max_length=160,blank=True,null=True, help_text="Description of campaign")
    commodities = models.ManyToManyField(Commodity, blank=True, null=True, help_text="Supplies to be distributed during campaign")
    shipments = models.ManyToManyField(Shipment, blank=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def get_active_campaign(klass):
        try:
            active = klass.objects.get(begin_date__lte=datetime.datetime.now().date(),\
                end_date__gte=datetime.datetime.now().date())
            return active
        # TODO better error handling!
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            return False 

    @property
    def commodities_str(self):
        commodities_str = [x.__unicode__() for x in self.commodities.all()]
        return ','.join(commodities_str)

    def __unicode__(self):
        return "%s (%s to %s)" % (self.name, self.begin_date, self.end_date)

class Campaign(CampaignBase):
    __metaclass__ = ExtensibleModelBase
