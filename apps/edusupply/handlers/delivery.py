#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import datetime

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Max
from django.contrib.contenttypes.models import ContentType

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from edusupply.models import School
from logistics.models import Facility

import utils

from logistics.models import Commodity
from logistics.models import Cargo
from logistics.models import Shipment
from logistics.models import ShipmentSighting
from logistics.models import ShipmentRoute


class DeliveryHandler(KeywordHandler):
    """
    """

    keyword = "rec|received|receive|recieve|recieved|got"

    def help(self):
        self.respond("DON'T PANIC")

    def handle(self, text):
        # expected format:
        #
        # recieved   books   123450   4   1
        #    |         |       |  |   |   |
        #    V         |       |  |   |   |
        # handler      V       |  |   |   |
        #           commodity  |  |   |   |
        #                      V  |   |   |
        #            school code  |   |   |
        #                         V   |   |
        #               satellite #   |   |
        #                             V   |
        #                    # of units   |
        #                                 V
        #                          condition code

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
                    self.respond("Sorry, I don't recognize your phone number. Please respond with your surname, facility (school or DEO) code, and facility name.")
        else:
            self.debug('NO IDENTITY')

        if known_contact is not None:
            self.debug('KNOWN PERSON')

            expected_tokens = ['word', 'number', 'number', 'number']
            token_labels = ['commodity', 'school_code', 'quantity', 'condition']
            tokens = utils.split_into_tokens(expected_tokens, token_labels, text)

            self.debug(tokens)

            if not tokens['commodity'].isdigit():
                def get_commodity(token):
                    try:
                        # lookup commodity by slug
                        com = Commodity.objects.get(slug__istartswith=tokens['commodity'])
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
                    self.respond("Sorry %s, no record of supply called '%s'" % (known_contact.name, tokens['commodity']))
                    self.respond("Approved supplies are %s" % ", ".join(Commodity.objects.values_list('slug', flat=True)))


            if tokens['school_code'].isdigit():

                def list_possible_schools_for_code(school_num):
                    possible_schools = School.objects.filter(code=school_num)
                    if not possible_schools:
                        return None
                    else:
                        # format a list containing 
                        #     1) combined school code + satellite_number
                        #     2) school name in parentheses
                        possible_school_list =\
                            [str(s[0]) + str(s[1]) + " (" + s[2] + ")" for s in\
                            possible_schools.values_list('code', 'satellite_number', 'name')]

                        return possible_school_list

                # school code should be between 1 and 5 digits,
                # and satellite_number should be 1 digit.
                # in the interest of not hardcoding anything, lets hit the db!
                max_codes = School.objects.aggregate(max_code=Max('code'),\
                    max_sat=Max('satellite_number'))
                max_code_length = len(str(max_codes['max_code']))
                max_sat_length = len(str(max_codes['max_sat']))

                if len(tokens['school_code']) <= (max_code_length + max_sat_length):
                    # separate school's code and satellite_number (last digit)
                    school_num = tokens['school_code'][:-1]
                    sat_num = tokens['school_code'][-1:]
                    try:
                        school = School.objects.get(code=school_num,\
                            satellite_number=sat_num)
                        facility, f_created = Facility.objects.get_or_create(location_id=school.pk,\
                            location_type=ContentType.objects.get(model='school'))

                    except ObjectDoesNotExist:
                        self.respond("Sorry %s, no record of school with code '%s'" % (known_contact.name, tokens['school_code']))

                        # maybe satellite number is omitted, so lookup schools by entire token
                        suggestions = list_possible_schools_for_code(tokens['school_code'])
                        if suggestions is not None:
                            self.respond("Did you mean one of: %s?" %\
                                (", ".join(suggestions)))

                        # maybe satellite number is incorrect, so lookup schools only by school_code
                        suggestions = list_possible_schools_for_code(school_num)
                        if suggestions is not None:
                            self.respond("Did you mean one of: %s?" %\
                                (", ".join(suggestions)))


                else:
                    self.respond("Sorry code '%s' is not valid. All codes are fewer than 6 digits" % (tokens['school_code']))

                #TODO acceptible values should be configurable
                #if int(tokens['quantity']) in range(1,10):
                #    if int(tokens['condition']) in range(1,4):
                if tokens['quantity'].isdigit():
                    if tokens['condition'].isdigit():
                        # map expected condition tokens into choices for db
                        conditions_map = {'1':'G', '2':'D', '3':'L'}

                        if facility is not None:
                            active_shipment = Facility.get_active_shipment(facility)

                            if active_shipment is not None:
                                # create a new Cargo object
                                observed_cargo = Cargo.objects.create(\
                                    commodity=commodity,\
                                    quantity=int(tokens['quantity']),\
                                    condition=conditions_map[tokens['condition']])

                                # create a new ShipmentSighting
                                sighting = ShipmentSighting.objects.create(\
                                    observed_cargo=observed_cargo,\
                                    seen_by=known_contact,\
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
                                    "%s pallets"        % (observed_cargo.quantity or "??"),
                                    "of %s"             % (commodity.slug or "??"),
                                    "to %s"             % (facility.location.name or "??"),
                                    "in %s condition"   % (observed_cargo.get_condition_display() or "??")
                            ]
                            confirmation = "Thanks %s. Confirmed delivery of %s." %\
                                (known_contact.name, " ".join(data))

                            self.respond(confirmation)


        #self.respond("WORD UP!")
