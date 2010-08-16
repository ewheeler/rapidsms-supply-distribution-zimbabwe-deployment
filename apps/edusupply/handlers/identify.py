#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact
from edusupply.models import School

import utils

class IdentifyHandler(KeywordHandler):
    """
    """

    keyword = "reg|register|id|identify"

    def help(self):
        self.respond("DON'T PANIC")

    def handle(self, text):
        # expected format:
        #
        # register  wheeler         3     unicef house
        #    |         |            |        |
        #    V         |            |        |
        # handler      V            |        |
        #           surname         |        |
        #                           V        |
        #                    facility code   |
        #                                    V
        #                              facility name

        known_contact = None
        possible_contacts_by_name = None
        possible_contacts = []
        facility = None
        possible_facilities = []
        possible_fac_by_code = None
        possible_fac_by_name = None
        fac_by_code = None
        fac_by_name = None

        if self.msg.connection.identity is not None:
            try:
                known_contact = Contact.objects.get(phone=self.msg.connection.identity)
                self.msg.connection.contact = known_contact
                self.msg.connection.save()
                self.debug('KNOWN CONTACT')
            except MultipleObjectsReturned:
                #TODO do something?
                self.debug('MULTIPLE IDENTITIES')
                pass
            except ObjectDoesNotExist:
                self.debug('NO PERSON FOUND')
        else:
            self.debug('NO IDENTITY')

        if True:
            expected_tokens = ['word', 'number', 'words']
            token_labels = ['surname', 'facility_code', 'facility_name']
            tokens = utils.split_into_tokens(expected_tokens, token_labels, text)

            self.debug(tokens)

            if not tokens['surname'].isdigit():
                possible_contacts_by_name = Contact.closest_by_name(tokens['surname'])
                if len(possible_contacts_by_name) == 1:
                    known_contact = possible_contacts_by_name[0][1]
                    self.msg.connection.contact = known_contact
                    self.msg.connection.save()

                possible_contacts_by_sound = Contact.closest_by_sound(tokens['surname'])
                if len(possible_contacts_by_sound) == 1:
                    known_contact = possible_contacts_by_sound[0][0]
                    self.msg.connection.contact = known_contact
                    self.msg.connection.save()

            if tokens['facility_code'].isdigit():
                possible_fac_by_code = School.closest_by_code(tokens['facility_code'])
                self.debug("%s possible facilities by code" % (str(len(possible_fac_by_code))))
                if len(possible_fac_by_code) == 1:
                    if possible_fac_by_code[0][2] == 0 and possible_fac_by_code[0][3] == 0 and possible_fac_by_code[0][4] == 1.0:
                        self.debug('PERFECT LOC MATCH BY CODE')
                        fac_by_code = possible_fac_by_code[0][1]

            if not tokens['facility_name'].isdigit():
                possible_fac_by_name = School.closest_by_name(tokens['facility_name'])
                self.debug("%s possible facilities by name" % (str(len(possible_fac_by_name))))
                if len(possible_fac_by_name) == 1:
                    if possible_fac_by_name[0][2] == 0 and possible_fac_by_name[0][3] == 0 and possible_fac_by_name[0][4] == 1.0:
                        self.debug('PERFECT LOC MATCH BY NAME')
                        fac_by_name = possible_fac_by_name[0][1]


            # see if either facility lookup returned a perfect match
            if fac_by_code or fac_by_name is not None:
                if fac_by_code and fac_by_name is not None:
                    # if they are both the same perfect match we have a winner
                    if fac_by_code.pk == fac_by_name.pk:
                        facility = fac_by_code
                    # if we have two different perfect matches, add to list
                    else:
                        possible_facilities.append(fac_by_code)
                        self.debug("%s possible facilities" % (str(len(possible_facilities))))
                        possible_facilities.append(fac_by_name)
                        self.debug("%s possible facilities" % (str(len(possible_facilities))))
                else:
                    # perfect match by either is also considered a winner
                    facility = fac_by_code if fac_by_code is not None else fac_by_name
                    self.debug(facility)

            # neither lookup returned a perfect match
            else:
                # make list of facility objects that are in both fac_by_code and fac_by_name
                if possible_fac_by_code and possible_fac_by_name is not None:
                    possible_facilities.extend([l[1] for l in filter(lambda x:x in possible_fac_by_code, possible_fac_by_name)])
                    self.debug("%s possible facilities by both" % (str(len(possible_facilities))))

                if len(possible_facilities) == 0:
                    possible_facilities.extend([l[1] for l in possible_fac_by_code if possible_fac_by_code is not None])
                    possible_facilities.extend([l[1] for l in possible_fac_by_name if possible_fac_by_name is not None])
                    self.debug("%s possible facilities by both" % (str(len(possible_facilities))))

                if len(possible_facilities) == 1:
                    facility = possible_facilities[0]

            if known_contact is None:
                if possible_contacts_by_name is not None:
                    possible_contacts_by_both = []
                    # gather the Contacts from the match tuples
                    possible_contacts = [c[1] for c in possible_contacts_by_name] 
                    self.debug("%s possible contacts by name" % (str(len(possible_contacts))))
                    self.debug(possible_contacts)

                    # add Contacts from phonetic match tuples
                    [possible_contacts.append(c[0]) for c in possible_contacts_by_sound]
                    self.debug("%s possible contacts by name" % (str(len(possible_contacts))))
                    self.debug(possible_contacts)

                    # lookup all the contacts associated with each possible_facilities from above
                    possible_contacts_by_loc_raw = [list(f.facilitycontact.all()) for f in possible_facilities]
                    # flatten list
                    possible_contacts_by_loc = [item for sublist in possible_contacts_by_loc_raw for item in sublist]

                    self.debug("%s possible contacts by location" % (str(len(possible_contacts_by_loc))))
                    self.debug(possible_contacts_by_loc)

                    if len(possible_contacts_by_loc) > 0:
                        possible_contacts_by_both = filter(lambda x:x in possible_contacts, possible_contacts_by_loc)
                        self.debug("%s possible contacts by BOTH" % (str(len(possible_contacts_by_both))))

                    if len(possible_contacts_by_both) == 0:
                        possible_contacts_by_both.extend(possible_contacts)
                        if possible_contacts_by_loc:
                            possible_contacts_by_both.extend(possible_contacts_by_loc)
                            self.debug("%s possible contacts by BOTH" % (str(len(possible_contacts_by_both))))

                    if len(possible_contacts_by_both) == 1:
                        known_contact = possible_contacts_by_both[0]
                        known_contact.phone = self.msg.connection.identity
                        self.msg.connection.contact = known_contact
                        self.msg.connection.save()
                        known_contact.save()

                    else:
                        possible_contacts_names = [c.name for c in possible_contacts_by_both]
                        self.respond("Did you mean one of: %s?" % (", ".join(possible_contacts_names)))

            else:
                if facility is not None:
                    self.respond("Hello %s, this phone number is now registered for %s (code: %s)" %\
                        (known_contact.name, facility.name,\
                        str(facility.code) + str(facility.satellite_number)))
                else:
                    possible_facilities_names = [str(f.name) + " " +  str(f.code) + str(f.satellite_number) for f in possible_facilities]
                    self.respond("Hello %s, did you mean one of: %s?" %\
                        (known_contact.name, " ,".join(possible_facilities_names)))
