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

    keyword = "confirm|conferm|conf|confirmed|cnf|comfirm|comf"

    def help(self):
        self.respond("DON'T PANIC")

    def handle(self, text):
        # expected format:
        #
        # confirm   books   gwaai valley primary   4288    G
        #    |         |            |               |      |
        #    V         |            |               |      |
        # handler      V            |               |      |
        #           commodity       |               |      |
        #                           V               |      |
        #                      school name          |      |
        #                                           |      |
        #                                           |      |
        #                                           V      |
        #                                   school code    |
        #                                                  |
        #                                                  |
        #                                                  V
        #                                               status

        # declare variables intended for valid information 
        known_contact = None
        commodity = None
        quantity = None
        condition = None
        observed_cargo = None

        facility = None
        school = None
        possible_schools = []
        possible_by_code = None
        possible_by_name = None
        school_by_code = None
        school_by_name = None

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

            expected_tokens = ['word', 'words', 'number', 'word']
            token_labels = ['commodity', 'school_name', 'school_code', 'condition']
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
                try:
                    school = School.objects.get(name__istartswith=tokens['school_name'])
                    facility, f_created = Facility.objects.get_or_create(location_id=school.pk,\
                        location_type=ContentType.objects.get(model='school'))

                except MultipleObjectsReturned:
                    schools = School.objects.filter(name__istartswith=tokens['school_name'])
                    for school in schools:
                        possible_schools.append(school)
                except ObjectDoesNotExist:

                    possible_by_name = School.closest_by_spelling(tokens['school_name'])
                    self.debug("%s possible facilities by name" % (str(len(possible_by_name))))
                    self.debug(possible_by_name)
                    if len(possible_by_name) == 1:
                        if possible_by_name[0][2] == 0 and possible_by_name[0][3] == 0 and possible_by_name[0][4] == 1.0:
                            self.debug('PERFECT LOC MATCH BY NAME')
                            school_by_name = possible_by_name[0][1]

                            school = school_by_name
                            facility, f_created = Facility.objects.get_or_create(location_id=school.pk,\
                                location_type=ContentType.objects.get(model='school'))

                    else:
                        if possible_by_name is not None:
                            for fac in possible_by_name:
                                possible_schools.append(fac[1])

                if tokens['school_code'].isdigit():
                    possible_by_code = School.closest_by_code(tokens['school_code'])
                    self.debug("%s possible facilities by code" % (str(len(possible_by_code))))
                    if len(possible_by_code) == 1:
                        if possible_by_code[0][2] == 0 and possible_by_code[0][3] == 0 and possible_by_code[0][4] == 1.0:
                            self.debug('PERFECT LOC MATCH BY CODE')
                            school_by_code = possible_by_code[0][1]

                # see if either facility lookup returned a perfect match
                if school_by_code or school_by_name is not None:
                    if school_by_code and school_by_name is not None:
                        # if they are both the same perfect match we have a winner
                        if school_by_code.pk == school_by_name.pk:
                            school = school_by_code
                            facility, f_created = Facility.objects.get_or_create(location_id=school.pk,\
                                location_type=ContentType.objects.get(model='school'))
                        # if we have two different perfect matches, add to list
                        else:
                            possible_schools.append(school_by_code)
                            self.debug("%s possible facilities" % (str(len(possible_schools))))
                            possible_facilities.append(school_by_name)
                            self.debug("%s possible facilities" % (str(len(possible_schools))))
                    else:
                        # perfect match by either is also considered a winner
                        school = school_by_code if school_by_code is not None else school_by_name
                        facility, f_created = Facility.objects.get_or_create(location_id=school.pk,\
                            location_type=ContentType.objects.get(model='school'))
                        self.debug(facility)

            # neither lookup returned a perfect match
            else:
                # make list of facility objects that are in both fac_by_code and fac_by_name
                if possible_by_code and possible_by_name is not None:
                    possible_schools.extend([l[1] for l in filter(lambda x:x in possible_by_code, possible_by_name)])
                    self.debug("%s possible facilities by both" % (str(len(possible_schools))))

                if len(possible_schools) == 0:
                    possible_schools.extend([l[1] for l in possible_by_code if possible_by_code is not None])
                    possible_schools.extend([l[1] for l in possible_by_name if possible_by_name is not None])
                    self.debug("%s possible facilities by both" % (str(len(possible_schools))))

                if len(possible_schools) == 1:
                    school = possible_schools[0]
                    facility, f_created = Facility.objects.get_or_create(location_id=school.pk,\
                        location_type=ContentType.objects.get(model='school'))

                if facility is None:
                    self.respond("Sorry I don't know '%s'" % (tokens['school_name']))
                    self.respond("Did you mean one of: %s?" %\
                        (", ".join(possible_schools)))

            if facility is not None:
                #TODO acceptible values should be configurable
                #if int(tokens['quantity']) in range(1,10):
                #    if int(tokens['condition']) in range(1,4):
                if not tokens['condition'].isdigit():

                    if facility is not None:
                        active_shipment = Facility.get_active_shipment(facility)

                        if active_shipment is not None:
                            # create a new Cargo object
                            condition = tokens['condition'].upper()
                            if condition in ['G', 'D', 'L', 'I']:
                                observed_cargo = Cargo.objects.create(\
                                    commodity=commodity,\
                                    condition=condition)
                            else:
                                self.respond("Oops. Status must be one of: G, D, L, or I")

                            seen_by_str = self.msg.connection.backend.name + ":" + self.msg.connection.identity

                            # create a new ShipmentSighting
                            sighting = ShipmentSighting.objects.create(\
                                observed_cargo=observed_cargo,\
                                facility=facility, seen_by=seen_by_str)

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

                            if observed_cargo.condition is not None:
                                this_school = School.objects.get(pk=facility.location_id)
                                map = {'G':1, 'D':-2, 'L':-3, 'I':-4}
                                if observed_cargo.condition in ['D', 'L', 'I', 'G']:
                                    this_school.status = map[observed_cargo.condition]
                                else:
                                    this_school.status = 0
                                this_school.save()
                                this_district = this_school.parent
                                # TODO optimize! this is too slow
                                updated = this_district.spark

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
