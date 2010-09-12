#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Max
from django.contrib.contenttypes.models import ContentType

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from edusupply.models import School

import utils

from logistics.models import Facility
from logistics.models import Campaign
from logistics.models import Commodity
from logistics.models import Cargo
from logistics.models import Shipment
from logistics.models import ShipmentSighting
from logistics.models import ShipmentRoute


class ConfirmationHandler(KeywordHandler):
    """
    """

    keyword = "confirm|conferm|conf|confirmed|cnf"

    def help(self):
        self.respond("DON'T PANIC")

    def handle(self, text):
        # expected format:
        #
        # confirm   books   gwaai       1
        #    |         |       |        |
        #    V         |       |        |
        # handler      V       |        |
        #           commodity  |        |
        #                      V        |
        #            school code        |
        #                               |
        #                               |
        #                               V
        #                         condition code

        # declare variables intended for valid information 
        known_contact = None
        commodity = None
        facility = None
        quantity = None
        condition = None
        observed_cargo = None

        if self.msg.contact is not None:
            self.debug(self.msg.contact)
            known_contact = self.msg.contact

        elif self.msg.connection.identity is not None:
            try:
                known_contact = Contact.objects.get(phone=self.msg.connection.identity)
                self.msg.connection.contact = known_contact
                self.msg.connection.save()
            except MultipleObjectsReturned:
                #TODO do something?
                self.debug('MULTIPLE IDENTITIES')
                pass
            except ObjectDoesNotExist:
                self.debug('NO PERSON FOUND')
                try:
                    known_contact = Contact.objects.get(alternate_phone=\
                        self.msg.connection.identity)
                    self.msg.connection.contact = known_contact
                    self.msg.connection.save()
                except MultipleObjectsReturned:
                    #TODO this case may be unneccesary, since many many contacts
                    # often share a single alternate_phone
                    self.debug('MULTIPLE IDENTITIES AFTER UNKNOWN')
                    pass
                except ObjectDoesNotExist:
                    #self.respond("Sorry, I don't recognize your phone number. Please respond with your surname, facility (school or DEO) code, and facility name.")
                    pass
            finally:
                known_contact = Contact.objects.create(phone=self.msg.connection.identity)
        else:
            self.debug('NO IDENTITY')

        if known_contact is not None:
            self.debug('KNOWN PERSON')

            expected_tokens = ['word', 'words', 'number']
            token_labels = ['commodity', 'school_name', 'condition']
            tokens = utils.split_into_tokens(expected_tokens, token_labels, text)

            self.debug(tokens)

            if not tokens['commodity'].isdigit():
                def get_commodity(token):
                    try:
                        # lookup commodity by slug
                        com = Commodity.objects.get(slug__istartswith=tokens['commodity'])
                        return com
                    except MultipleObjectsReturned:
                        #TODO do something here?
                        pass
                    except ObjectDoesNotExist:
                        coms = Commodity.objects.all()
                        for com in coms:
                            # iterate all commodities and see if submitted
                            # token is in an aliases list
                            match = com.has_alias(token)
                            if match is not None:
                                if match:
                                    return com
                            continue
                        return None

                commodity = get_commodity(tokens['commodity'])

                if commodity is None:
                    self.respond("Sorry, no supply called '%s'" % (tokens['commodity']))
                    self.respond("Approved supplies are %s" % ", ".join(Commodity.objects.values_list('slug', flat=True)))


            if not tokens['school_name'].isdigit():
                possible_school_names = []
                try:
                    school = School.objects.get(name__istartswith=tokens['school_name'])
                    facility, f_created = Facility.objects.get_or_create(location_id=school.pk,\
                        location_type=ContentType.objects.get(model='school'))

                except MultipleObjectsReturned:
                    schools = School.objects.filter(name__istartswith=tokens['school_name'])
                    for school in schools:
                        possible_school_names.append(school.name)
                except ObjectDoesNotExist:

                    possible_fac_by_name = School.closest_by_spelling(tokens['school_name'])
                    self.debug("%s possible facilities by name" % (str(len(possible_fac_by_name))))
                    self.debug(possible_fac_by_name)
                    if len(possible_fac_by_name) == 1:
                        if possible_fac_by_name[0][2] == 0 and possible_fac_by_name[0][3] == 0 and possible_fac_by_name[0][4] == 1.0:
                            self.debug('PERFECT LOC MATCH BY NAME')
                            fac_by_name = possible_fac_by_name[0][1]

                            school = fac_by_name
                            facility, f_created = Facility.objects.get_or_create(location_id=school.pk,\
                                location_type=ContentType.objects.get(model='school'))

                    else:
                        if possible_fac_by_name is not None:
                            for fac in possible_fac_by_name:
                                possible_school_names.append(fac[1].name)
                if facility is None:
                    self.respond("Did you mean one of: %s?" %\
                        (", ".join(possible_school_names)))

            else:
                self.respond("Sorry I don't know '%s'" % (tokens['school_name']))

            if facility is not None:
                #TODO acceptible values should be configurable
                #if int(tokens['quantity']) in range(1,10):
                #    if int(tokens['condition']) in range(1,4):
                if tokens['condition'].isdigit():
                    # map expected condition tokens into choices for db
                    conditions_map = {'1':'G', '2':'D', '3':'L', '4':'I'}

                    if facility is not None:
                        active_shipment = Facility.get_active_shipment(facility)

                        if active_shipment is not None:
                            # create a new Cargo object
                            observed_cargo = Cargo.objects.create(\
                                commodity=commodity,\
                                condition=conditions_map[tokens['condition']])

                            if observed_cargo.condition is not None:
                                this_school = School.objects.get(pk=facility.location_id)
                                if observed_cargo.condition in ['D', 'L', 'I']:
                                    this_school.status = -1
                                elif observed_cargo.condition == 'G':
                                    this_school.status = 1
                                else:
                                    this_school.status = 0

                            # create a new ShipmentSighting
                            sighting = ShipmentSighting.objects.create(\
                                observed_cargo=observed_cargo,\
                                facility=facility)

                            # associate new Cargo with Shipment
                            active_shipment.status = 'D'
                            active_shipment.actual_delivery_time=datetime.datetime.now()
                            active_shipment.cargos.add(observed_cargo)
                            active_shipment.save()

                            # get or create a ShipmentRoute and associate
                            # with new ShipmentSighting
                            route, new_route = ShipmentRoute.objects.get_or_create(\
                                shipment=active_shipment)
                            route.sightings.add(sighting)
                            route.save()

                            campaign = Campaign.get_active_campaign()
                            if campaign is not None:
                                campaign.shipments.add(active_shipment)
                                campaign.save()

                        data = [
                                "of %s"             % (commodity.slug or "??"),
                                "to %s"             % (facility.location.name or "??"),
                                "in %s condition"   % (observed_cargo.get_condition_display() or "??")
                        ]
                        confirmation = "Thanks. Confirmed delivery of %s." %\
                            (" ".join(data))

                        self.respond(confirmation)


        #self.respond("WORD UP!")
