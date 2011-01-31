#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import re
import itertools
import copy
import datetime
from exceptions import StopIteration

from django.contrib.contenttypes.models import ContentType

from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message

from edusupply.models import School
from edusupply.models import District 
from edusupply.models import Province 
from edusupply.models import Country 
from edusupply.models import Confirmation

from logistics.models import Facility
from logistics.models import Campaign
from logistics.models import Commodity
from logistics.models import Cargo
from logistics.models import Shipment
from logistics.models import ShipmentSighting
from logistics.models import ShipmentRoute

def consume_in_reverse(list):
    while len(list) != 0:
        yield list.pop()

def letters_for_numbers(str):
    # dict of letters and the numerals they are intended to be 
    gaffes = {'i' : '1', 'l' : '1', 'o' : '0'}

    # don't worry about case
    numeralized = str.lower()

    for g in gaffes.iterkeys():
        try:
            # replace each of the letters with its appropriate numeral
            numeralized = numeralized.replace(g, gaffes[g])
        except Exception, e:
            print e
    # return the string once all gaffes have been replaced
    return numeralized 

def reconcile_condition(token):
    if token.isalpha():
        if len(token) == 1:
            if token.upper() in ["G", "I", "D", "L"]:
                return token.upper()
            else:
                return None
        else:
            if token.upper() == "GOOD":
                return "G"
            elif token.upper() == "INCOMPLETE":
                return "I"
            elif token.upper() == "DAMAGED":
                return "D"
            elif token.upper() in ["ALTERNATE", "LOCATION"]:
                return "L"
            else:
                return None
    else:
        return None

def reconcile_school_by_code(token):
    if token.isdigit():
        # using 3 or 4 for length, because here is the distribution of len(code):
        # len(code) | frequency out of 5572 schools
        #    1      |     18
        #    2      |    159
        #    3      |    240
        #    4      |   5131
        #    5      |     24
        if len(token) in [3, 4]:
            possible_by_code = School.closest_by_code(token)
            if len(possible_by_code) == 1:
                if possible_by_code[0][2] == 0 and possible_by_code[0][3] == 0 and possible_by_code[0][4] == 1.0:
                    return possible_by_code[0][1]
            else:
                return possible_by_code
        else:
            return None
    else:
        return None

def reconcile_school_by_spelling(token):
    possible_by_name = School.closest_by_spelling(token)
    if len(possible_by_name) == 1:
        if possible_by_name[0][2] == 0 and possible_by_name[0][3] == 0 and possible_by_name[0][4] == 1.0:
            return possible_by_name[0][1]
    else:
        return possible_by_name

def go():
    print datetime.datetime.now().isoformat()
    clean_db = True
    if clean_db:
        schools = School.objects.all().update(status=0)
        print "reset schools"
        districts = District.objects.all().update(status=None)
        print "reset districts"
        shipments = Shipment.objects.all().update(status='P')
        shipments = Shipment.objects.all().update(actual_delivery_time=None)
        print "reset shipments"
        sightings = ShipmentSighting.objects.all().delete()
        print "deleted sightings"
        routes = ShipmentRoute.objects.all().delete()
        print "deleted routes"
        cargos = Cargo.objects.all().delete()
        print "deleted cargos"
    incoming = Message.objects.filter(direction='I')
    unique_text = []
    unique = []
    # make list of unique incoming messages, based on the message text
    for mess in incoming:
        if mess.text not in unique_text:
            unique_text.append(mess.text)
            unique.append(mess)

    # all school names, split into individual words,
    # flattened into 1-d list, duplicates removed
    school_name_words = list(set(list(itertools.chain.from_iterable([n.split() for n in School.objects.all().values_list('name', flat=True)]))))

    # odd punctuation we want to get rid of
    junk = ['.', ',', '\'', '\"', '`', '(', ')', ':', ';', '&', '?', '!', '~', '`', '+', '-']
    school_name_words_no_punc = []
    for mark in junk:
        for word in school_name_words:
            # remove punctuation from school name words, because we'll be
            # removing the same punctuation from message text
            school_name_words_no_punc.append(word.replace(mark, " "))

    # if user has spelled out any of the conditions, we want to see those,
    # as well as "L" -- other conditions "G", "D", "I" already appear in school_name_words_no_punc
    other_words = ["INCOMPLETE", "GOOD", "DAMAGED", "ALTERNATE", "LOCATION", "L"]
    ok_words = school_name_words_no_punc + other_words

    print len(unique)
    counter = 0
    matches = 0
    #for text in ['CONFIRM BOOKS DADATA PRIMARY 1196i']:
    #for msg in unique[45:55]:
    for msg in unique:
        counter = counter + 1
        if counter % 100 == 0:
            print "loop: %s" % str(counter)
        text = msg.text
        text_list = []

        # replace any creative punctuation with spaces
        for mark in junk:
            text = text.replace(mark, " ")

        # split the text into chunks around spaces
        blobs = text.split(" ")
        for blob in blobs:
            clean_blob = blob
            try:
                if blob[-1:].isalpha() and blob[:-1].isdigit():
                    # if theres somthing like '1234g'
                    # add as two separate blobs: '1234' and 'g'
                    text_list.append(blob[:-1])
                    text_list.append(blob[-1:])
                    # and move on to next blob before
                    # letters_for_numbers might duplicate it incorrectly
                    continue
            except IndexError:
                pass
            for n in range(3):
                # clean up blobs only if they have a digit in the first few
                # characters -- so we don't clean up things like user1
                try:
                   if blob[n].isdigit():
                        clean_blob = letters_for_numbers(blob)
                        break
                except IndexError:
                   # if the blob doesnt have the first few characters,
                   # and there is no digit yet, move on
                   break
            # add the cleaned blob (or untouched blob) to a running list
            text_list.append(clean_blob)


        relevant = []
        # now, loop through cleaned words and keep relevant ones
        for word in text_list:
            if word.isdigit():
                relevant.append(word)
                continue
            if word.upper() in ok_words:
                relevant.append(word)
                continue
        # attach list of relevant bits to message
        confirmation = Confirmation(message=msg)
        confirmation.token_list = copy.copy(relevant)
        confirmation.save()

        # now try to make sense of these tokens
        consumed = []
        unconsumed = []

        # generator to yield relevant items in reverse order
        consume = consume_in_reverse(relevant)
        condition = None
        school = None
        school_by_code = None
        school_by_spelling = None
        try:
            def attempt_consumption_of_condition_and_code(condition, school_by_code):
                token = consume.next()

                if condition is None:
                    condition = reconcile_condition(token)
                    if condition is not None:
                        consumed.append(token)
                    else:
                        if token not in unconsumed:
                            unconsumed.append(token)

                # if the last token (the first we have examined) this time
                # has been consumed, pop the next-to-last token.
                # otherwise, we will continue with the last token
                if token in consumed:
                    token = consume.next()

                # note this may be a school object or a list of tuples
                # in the format:
                # ('token', school_obj, lev_edit_int, dl_edit_int, jw_float)
                if school_by_code is None:
                    school_by_code = reconcile_school_by_code(token)
                    if school_by_code is not None:
                        consumed.append(token)
                    else:
                        if token not in unconsumed:
                            unconsumed.append(token)

                if len(consumed) == 2:
                    return condition, school_by_code
                else:
                    return attempt_consumption_of_condition_and_code(condition, school_by_code)

            # recursively consume tokens until we have something for condition and school_by_code
            condition, school_by_code = attempt_consumption_of_condition_and_code(condition, school_by_code)

            if not isinstance(school_by_code, list):
                # woo! we have a condition and a single school, this is probably
                # enough to be sure about the school, so save it as school before
                # exploding into finding the school name
                school = school_by_code
                confirmation.school = school
                confirmation.save()

            try:
                school_name = None
                # pop the next-to-next-to-last token
                token = consume.next()

                # now lets try to get the school name
                if token in consumed:
                    token = consume.next()

                school_name = token
                consumed.append(token)

                # consume up to five additional tokens and
                # prepend to school_name
                token = consume.next()
                if token.isalpha():
                    school_name = token + " " + school_name
                    consumed.append(token)
                else:
                    unconsumed.append(token)
                token = consume.next()
                if token.isalpha():
                    school_name = token + " " + school_name
                    consumed.append(token)
                else:
                    unconsumed.append(token)
                token = consume.next()
                if token.isalpha():
                    school_name = token + " " + school_name
                    consumed.append(token)
                else:
                    unconsumed.append(token)
                token = consume.next()
                if token.isalpha():
                    school_name = token + " " + school_name
                    consumed.append(token)
                else:
                    unconsumed.append(token)
                token = consume.next()
                if token.isalpha():
                    school_name = token + " " + school_name
                    consumed.append(token)
                else:
                    unconsumed.append(token)

            except StopIteration:
                if school_name is not None:
                    school_by_spelling = reconcile_school_by_spelling(school_name.strip())

                p_schools = []
                if isinstance(school_by_code, list):
                    for s in (t[1] for t in school_by_code):
                        if s not in p_schools:
                            p_schools.append(s)
                if school_by_spelling is not None:
                    if not isinstance(school_by_spelling, list):
                        if school is not None:
                            if school.code == school_by_spelling.code:
                                pass
                            else:
                                p_schools.append(school_by_spelling)
                        else:
                            school = school_by_spelling
                    else:
                        for s in (t[1] for t in school_by_spelling):
                            if s is not None:
                                if s.code not in [p.code for p in p_schools if p is not None]:
                                    p_schools.append(s)
                                else:
                                    school = s

                # if we have no sure match, and a list of possible schools
                # returned by reconcile_school_by_spelling, try toggling
                # the word primary
                if school is None and isinstance(school_by_spelling, list):
                    uschool_name = school_name.upper()
                    if uschool_name.find("PRIMARY") != -1:
                        edited_name = uschool_name.replace("PRIMARY", "")
                    else:
                        edited_name = uschool_name + " PRIMARY"

                    school_by_spelling = reconcile_school_by_spelling(edited_name.strip())
                    if school_by_spelling is not None:
                        if not isinstance(school_by_spelling, list):
                            if school is not None:
                                if school.code == school_by_spelling.code:
                                    pass
                                else:
                                    p_schools.append(school_by_spelling)
                            else:
                                school = school_by_spelling
                        else:
                            for s in (t[1] for t in school_by_spelling):
                                if s.code not in [p.code for p in p_schools]:
                                    p_schools.append(s)
                                else:
                                    school = s

                if school is not None:
                    if condition is not None:
                        confirmation.condition = condition
                        confirmation.valid = True
                        confirmation.save()
                        matches = matches + 1
                        if matches % 20 == 0:
                            print "MATCHES: %s out of %s" % (str(matches), str(counter))
                            print datetime.datetime.now().isoformat()

                        commodity = Commodity.objects.get(slug__istartswith="textbooks")
                        facility, f_created = Facility.objects.get_or_create(location_id=school.pk,\
                            location_type=ContentType.objects.get(model='school'))
                        if facility is not None:
                            active_shipment = Facility.get_active_shipment(facility)
                            observed_cargo = Cargo.objects.create(\
                                commodity=commodity,\
                                condition=condition)

                            seen_by_str = msg.connection.backend.name + ":" + msg.connection.identity
                            # create a new ShipmentSighting
                            sighting = ShipmentSighting.objects.create(\
                                observed_cargo=observed_cargo,\
                                facility=facility, seen_by=seen_by_str)

                            # associate new Cargo with Shipment
                            active_shipment.status = 'D'
                            active_shipment.actual_delivery_time=msg.date
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
                                # map reported condition to the status numbers
                                # that the sparklines will use
                                map = {'G':1, 'D':-2, 'L':-3, 'I':-4}
                                if observed_cargo.condition in ['D', 'L', 'I', 'G']:
                                    this_school.status = map[observed_cargo.condition]
                                else:
                                    this_school.status = 0
                                this_school.save()
                                this_district = this_school.parent
                                # TODO optimize! this is very expensive
                                # and way too slow
                                # re-generate the list of statuses that
                                # the sparklines will use
                                #updated = this_district.spark

                            campaign = Campaign.get_active_campaign()
                            if campaign is not None:
                                campaign.shipments.add(active_shipment)
                                campaign.save()

                        '''
                        data = [
                                "of %s"             % (commodity.slug or "??"),
                                "to %s"             % (facility.location.name or "??"),
                                "in %s condition"   % (observed_cargo.get_condition_display() or "??")
                        ]
                        confirmation = "Thanks. Confirmed delivery of %s." %\
                            (" ".join(data))
                        print seen_by_str + " " + confirmation
                        '''

        except StopIteration:
            continue
        except Exception, e:
            print e
            print counter
            print matches
            import ipdb;ipdb.set_trace()
    print "MATCHES: %s" % str(matches)
    districts = District.objects.all()
    print "%s districts" % str(districts.count())
    for d in districts:
        print "updating sparks for '%s'" % d.name
        d.spark

'''
1587 total incoming messages
    746 unique phone numbers

1046 unique incoming messages (541 duplicates 34%)
    757 parsed successfully
        47.7% of total (1587)
        72.4% of uniques (1046)
        363 unique schools
'''
