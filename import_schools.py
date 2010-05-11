#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
import sys
import os
import codecs
import csv
import datetime
import re
from decimal import Decimal as D

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import setup_environ

try:
    import settings
    setup_environ(settings)
except:
    sys.exit("No settings found")


from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from rapidsms.contrib.locations.models import LocationType
from rapidsms.contrib.locations.models import Point

def import_csv(args):

    # use codecs.open() instead of open() so all characters are utf-8 encoded
    # BEFORE we start dealing with them (just in case)
    # rU option is for universal-newline mode which takes care of \n or \r etc
    csvee = codecs.open("zim_schools.csv", "rU", encoding='utf-8', errors='ignore')

    # sniffer attempts to guess the file's dialect e.g., excel, etc
    dialect = csv.Sniffer().sniff(csvee.read(1024))
    # for some reason, sniffer was finding '"'
    dialect.quotechar = '"'
    csvee.seek(0)
    # DictReader uses first row of csv as key for data in corresponding column
    reader = csv.DictReader(csvee, dialect=dialect, delimiter=",",\
        quoting=csv.QUOTE_ALL, doublequote=True)

    countries = LocationType.objects.create(singular="Country", plural="Countries",\
        slug="countries")
    country, c_created = Location.objects.get_or_create(name="Zimbabwe",\
        type_id=countries.pk)

    provinces = LocationType.objects.create(singular="Province",\
        plural="Provinces", slug="provinces", exist_in=country.pk)

    #TODO calculate per-pallet weight
    commodity = Commodity(name="Textbooks", slug="textbooks", unit="PL")

    satellite_counter = 0
    school_counter = 0

    try:
        print 'begin rows'
        po_count = 0
        for row in reader:
            def has_datum(row, key):
                if row.has_key(key):
                    if row[key] != "":
                        return True
                return False

            def has_data(row, key_list):
                if False in [has_datum(row, key) for key in key_list]:
                    return False
                else:
                    return True

            def clean_phone(raw_phone):
                if raw_phone in ['NIL']:
                    return None
                else:
                    cleaned = re.sub("[^0-9]", "", raw_phone) 
                    return cleaned

            if has_datum(row, 'ProvName'):
                province, created = Location.objects.get_or_create(\
                    name=row['ProvName'], type_id=provinces.pk)

                if has_data(row, ['DistName', 'DistCode']):
                    districts, created = LocationType.objects.get_or_create(\
                        singular='District', plural='Districts',\
                        slug='districts', exists_in=province.pk)
                    district = Location.objects.create(name=row['DistName',\
                        type_id=districts.pk, code=row['DistCode'])

                    if has_data(row, ['deo', 'phone_number']):
                        try:
                            clean_phone_number = clean_phone(row['phone_number'])
                            deo = Contact.objects.create(name=row['deo'],\
                                    phone=clean_phone_number, district=district.pk)

                        except Exception, e:
                            print 'BANG deo:'
                            print e
                            print row
                            continue


                        if has_data(row, ['GPS_south', 'GPS_east']):
                            #TODO strip degree symbol?
                            try:
                                point = Point.objects.create(latitude=row['GPS_south'],\
                                            longitude=row['GPS_east'])

                            except Exception, e:
                                print 'BANG point:'
                                print e
                                print row
                                continue

                        else:
                            point = None
                            try:
                                schools, created = LocationType.objects.get_or_create(\
                                    singular='School', plural='Schools',\
                                    slug='schools', exists_in=district.pk)

                            except Exception, e:
                                print 'BANG schools:'
                                print e
                                print row
                                continue

                        if has_data(row, ['school_name', 'school_address', 'school_code', 'km_to_DEO', 'SchoolType']):
                            school_type = row['SchoolType']
                            #Actual School Code  + Identifier =    Final School Code
                            # e.g
                            # 04655              +        0   =     0465510

                            #   Key for Identifier
                            #   0 - Mother \ Registered School
                            #   1 - First Satellite School
                            #   2 - Second Satellite School
                            #   3 - Third Satellite School
                            #   (NOTE THAT THIS COULD GO UP TO 9 DEPENDING ON THE NUMBER OF SATELLITE SCHOOLS)

                            # TODO is this too crappy to work?
                            if school_type == 'REGISTERED':
                                satellite_code = 0
                            elif school_type == 'MOTHER':
                                satellite_code = 0
                                satellite_counter = 0
                            elif school_type == 'SATELLITE':
                                satellite_counter += 1
                                satellite_code = satellite_counter
                            else:
                                satellite_code = None

                            #TODO clean N/As from km_to_DEO

                            try:
                                school = Location.objects.create(name=row['school_name'],\
                                    address=row['school_address'], code=row['school_code'],\
                                    km_to_DEO=row['km_to_DEO'], type_id=schools.pk,\
                                    satellite_number=satellite_code)
                                school_counter += 1

                            except Exception, e:
                                print 'BANG school:'
                                print e
                                print row
                                print school_counter
                                continue

                            if has_data(row, ['contact_name', 'phone', 'alternate_phone']): 
                                try:
                                    clean_number = clean_phone(row['phone'])
                                    clean_alt_number = clean_phone(row['alternate_phone'])
                                    headmaster = Contact.objects.create(name=row['contact_name'],\
                                        phone=clean_number, alternate_phone=clean_alt_number,\
                                        school=school.pk)

                                except Exception, e:
                                    print 'BANG headmaster:'
                                    print e
                                    print row
                                    continue

                            if has_data(row, ['number_of_pallets', 'total_weight_of_pallets']):
                                try:
                                    cargo = Cargo.objects.create(commodity=commodity,\
                                                quantity=row['number_of_pallets'])

                                except Exception, e:
                                    print 'BANG cargo:'
                                    print e
                                    print row
                                    continue

                else:
                    print 'OOPS. MOVING ON'
                    continue
            continue


    except csv.Error, e:
        # TODO handle this error?
        print('%d : %s' % (reader.reader.line_num, e))


if __name__ == "__main__":
    import_csv(sys.argv) 
