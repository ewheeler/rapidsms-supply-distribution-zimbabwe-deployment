#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact

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
            except MultipleObjectsReturned:
                #TODO do something?
                self.debug('MULTIPLE IDENTITIES')
                pass
            except ObjectDoesNotExist:
                self.debug('NO PERSON FOUND')
        else:
            self.debug('NO IDENTITY')
        if known_contact is not None:
            self.respond("Oh i know you!")
        else:
            token_labels = ['surname', 'facility_code', 'facility_name']
            token_data = text.split()

            self.debug(token_data)

            if len(token_data) < len(token_labels):
                self.debug('NOT ENOUGH TOKENS')
            if len(token_data) > len(token_labels):
                self.debug('TOO MANY TOKENS')
                # if the third token is digits, condense the first
                # two tokens into one token
                if token_data[2].isdigit():
                    self.debug('MERGING SURNAME')
                    surname_tokens = token_data[:2]
                    surname = " ".join(surname_tokens)
                    del token_data[:2]
                    token_data.insert(0, surname)
                    self.debug(token_data)
                if len(token_data) > len(token_labels):
                # if we still have too many tokens, and digits are
                # in the right place, condense any following tokens
                # into one token
                    if token_data[1].isdigit():
                        self.debug('MERGING FACILITY NAME')
                        fac_name_tokens = token_data[2:] 
                        fac_name = " ".join(fac_name_tokens)
                        del token_data[2:]
                        token_data.append(fac_name)
                        self.debug(token_data)

            tokens = dict(zip(token_labels, token_data))
            if not tokens['surname'].isdigit():
                possible_contacts_by_name = Contact.closest_by_name(tokens['surname'])
                if len(possible_contacts) == 1:
                    known_contact = possible_contact[0][1]

            if tokens['facility_code'].isdigit():
                possible_fac_by_code = Location.closest_by_code(tokens['facility_code'])
                self.debug("%s possible facilities by code" % (str(len(possible_fac_by_code))))
                if len(possible_fac_by_code) == 1:
                    if possible_fac_by_code[0][2] == 0 and possible_fac_by_code[0][3] == 0 and possible_fac_by_code[0][4] == 1.0:
                        self.debug('PERFECT LOC MATCH BY CODE')
                        fac_by_code = possible_fac_by_code[0][1]

            if not tokens['facility_name'].isdigit():
                possible_fac_by_name = Location.closest_by_name(tokens['facility_name'])
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
                        self.debug("%s possible facilities by code" % (str(len(fac_by_code))))
                        possible_facilities.append(fac_by_name)
                        self.debug("%s possible facilities by name" % (str(len(fac_by_name))))
                else:
                    # perfect match by either is also considered a winner
                    facility = fac_by_code if fac_by_code is not None else fac_by_name

            # neither lookup returned a perfect match
            else:
                '''
                # see how close the closest matches are for each kind of lookup
                max_jw_code = max([c[3] for c in possible_fac_by_code])
                max_jw_name = max([n[3] for n in possible_fac_by_name])

                min_dl_code = min([c[2] for c in possible_fac_by_code])
                min_dl_name = min([n[2] for n in possible_fac_by_name])

                # see if one lookup performed a lot better than the other
                if abs(max_jw_code - max_jw_name) >= .2:
                    self.debug('BIG JW DIFF')

                if abs(min_dl_code - min_dl_name) >= 2:
                    self.debug('BIG DL DIFF')
                '''
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
                        known_contact.save()
                        if facility is not None:
                            self.respond("Hello %s, this phone number is now registered for %s (code: %s)" %\
                                (known_contact.name, facility.name,\
                                str(facility.code) + str(facility.satellite_number)))
                        else:
                            possible_facilities_names = [str(f.name) + " " +  str(f.code) + str(f.satellite_number) for f in possible_facilities]
                            self.respond("Hello %s, did you mean one of: %s?" %\
                                (known_contact.name, " ,".join(possible_facilities_names)))
                    else:
                        #possible_contacts_names = [c.name for c in possible_contacts_by_both]
                        possible_contacts_names = [c.name for c in possible_contacts_by_both]
                        self.respond("Did you mean one of: %s?" % (", ".join(possible_contacts_names)))

