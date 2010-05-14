#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Max

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.models import Contact
from logistics.models import Commodity


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
        known_person = None
        commodity = None
        facility = None
        quantity = None
        condition = None

        if self.msg.connection.identity is not None:
            try:
                known_person = Contact.objects.get(phone=self.msg.connection.identity)
            except MultipleObjectsReturned:
                #TODO do something?
                pass
            except ObjectDoesNotExist:
                try:
                    known_person  = Contact.objects.get(alternate_phone=\
                        self.msg.connection.identity)
                except MultipleObjectsReturned:
                    #TODO do something if this occurs?
                    pass
                except ObjectDoesNotExist:
                    #TODO handler for this response
                    self.respond("Sorry I don't recognize your phone number. Please respond with your surname and facility name.")

        if known_person is not None:
            token_labels = ['commodity', 'school_code', 'quantity', 'condition']
            token_data = text.split()

            if len(token_data) > 4:
                self.respond('Too many data!')
            elif len(token_data) < 4:
                self.respond('Not enough data!')
            else:
                tokens = dict(zip(token_labels, token_data))
                if not tokens['commodity'].isdigit():
                    try:
                        commodity = Commodity.objects.get(slug__istartswith=tokens['commodity'])

                    except MultipleObjectsReturned:
                        #TODO do something here?
                        pass

                    except ObjectDoesNotExist:
                        self.respond("Sorry no record of supply called '%s'" % tokens['commodity'])
                        self.respond("Approved supplies are %s" % ", ".join(Commodity.objects.values_list('slug', flat=True)))

                if tokens['school_code'].isdigit():

                    def list_possible_schools_for_code(school_num):
                        possible_schools = Location.objects.filter(code=school_num)
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
                    max_codes = Location.objects.aggregate(max_code=Max('code'),\
                        max_sat=Max('satellite_number'))
                    max_code_length = len(str(max_codes['max_code']))
                    max_sat_length = len(str(max_codes['max_sat']))

                    if len(tokens['school_code']) <= (max_code_lenth + max_sat_length):
                        # separate school's code and satellite_number (last digit)
                        school_num = tokens['school_code'][:-1]
                        sat_num = tokens['school_code'][-1:]
                        try:
                            facility = Location.objects.get(code=school_num,\
                                satellite_number=sat_num)

                        except ObjectDoesNotExist:
                            self.respond("Sorry no record of school with code %s" % (tokens['school_code']))

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
                            conditions_map = {'1':'G', '2':'D', '3':'L'}

                            if facility is not None:
                                active_shipment = Shipment.objects.filter(\
                                    destination=facility).exclude(status='D')
                                if active_shipment:
                                    observed_cargo = Cargo.objects.create(\
                                       commodity=commodity,\
                                       quantity=int(tokens['quantity']),\
                                       condition=conditions_map[tokens['condition']])

                                    sighting = ShipmentSighting.objects.create(\
                                        observed_cargo=observed_cargo,\
                                        seen_by=known_contact,\
                                        shipment=active_shipment,\
                                        location=facility)

                                    route = ShipmentRoute.objects.get_or_create(\
                                        shipment=active_shipment)
                                    route.sightings.add(sighting)
                                    route.save()

                                data = [
                                        "%s pallets"        % (observed_cargo.quantity or "??"),
                                        "of %s"             % (commodity.slug or "??"),
                                        "at %s"             % (facility.name or "??"),
                                        "in %s condition"   % (observed_cargo.get_condition_display or "??")
                                ]
                                confirmation = "Thanks %s. Confirmed delivery of %s." %\
                                    (known_contact.name, " ".join(data))

                                self.respond(confirmation)


        self.respond("WORD UP!")
