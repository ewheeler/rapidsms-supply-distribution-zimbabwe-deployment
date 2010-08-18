#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
import sys
import os
import codecs
import csv
import datetime
import re

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import setup_environ
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType

from decimal import Decimal as D
import decimaldegrees as dd

#try:
#    import settings
#    setup_environ(settings)
#except:
#    sys.exit("No settings found")


from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Point

from edusupply.models import School
from edusupply.models import District 
from edusupply.models import Province 
from edusupply.models import Country 

from logistics.models import Commodity
from logistics.models import Cargo
from logistics.models import Shipment
from logistics.models import Facility

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

    try:
        country, c_created = Country.objects.get_or_create(name="Zimbabwe",\
            slug=slugify("Zimbabwe"))

        #TODO calculate per-pallet weight
        commodity, c_created = Commodity.objects.get_or_create(name="Textbooks",\
            slug="textbooks", unit="PL", aliases="textbook,books,book")

        satellite_counter = 0
        school_counter = 0
    except Exception, e:
        print 'BANG initial objects'
        print e

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

            def only_digits(raw_str):
                cleaned = re.sub("[^0-9]", "", raw_str) 
                if cleaned != "":
                    return cleaned
                else:
                    return None

            if has_datum(row, 'ProvName'):
                province, created = Province.objects.get_or_create(\
                    name=row['ProvName'], slug=slugify(row['ProvName']),\
                    parent_id=country.pk, parent_type=ContentType.objects.get(model='country'))

                if has_data(row, ['DistName', 'DistCode']):
                    district, created = District.objects.get_or_create(name=row['DistName'],\
                        code=row['DistCode'], slug=slugify(row['DistName']),\
                        parent_id=province.pk, parent_type=ContentType.objects.get(model='province'))

                    if has_data(row, ['deo', 'phone_number']):
                        try:
                            clean_phone_number = only_digits(row['phone_number'])
                            deo, created = Contact.objects.get_or_create(name=row['deo'],\
                                    phone=clean_phone_number)
                            deo.districts.add(district)
                            deo.save()

                        except Exception, e:
                            print 'BANG deo:'
                            print e
                            print row
                            continue

                        def clean_and_convert_dm(raw_str):
                            # split degree and minute.decimal, remove minute mark (')
                            clean_dm = [x.strip('\'') for x in raw_str.split()]
                            # convert degree minute.decimal to degree.decimal
                            clean_dd = dd.dm2decimal(*clean_dm)
                            return clean_dd 

                        if has_data(row, ['GPS_south', 'GPS_east']):
                            # latitude coordinates from excel file are 
                            # all 'south' so degrees should be negative 
                            clean_GPS_south = clean_and_convert_dm(row['GPS_south']).copy_negate()
                            # longitude coordinates from excel file are
                            # all 'east' so degrees should remain positive
                            clean_GPS_east = clean_and_convert_dm(row['GPS_east'])
                            try:
                                point, created = Point.objects.get_or_create(latitude=clean_GPS_south,\
                                            longitude=clean_GPS_east)

                            except Exception, e:
                                print 'BANG point:'
                                print e
                                print row
                                continue

                        else:
                            point = None

                        if has_data(row, ['school_name', 'SchoolType']):
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

                            clean_km_to_DEO = only_digits(row['km_to_DEO'])

                            safe_address = row['school_address']
                            if safe_address in ["NIL", ""]:
                                safe_address = None

                            safe_code = row['school_code']
                            if safe_code in ["NIL", ""]:
                                safe_code = None

                            try:
                                school, created = School.objects.get_or_create(name=row['school_name'],\
                                    address=safe_address, code=safe_code,\
                                    km_to_DEO=clean_km_to_DEO, slug=slugify(row['school_name']),\
                                    satellite_number=satellite_code, point=point,\
                                    parent_id=district.pk, parent_type=ContentType.objects.get(model='district'))
                                school_counter += 1

                            except Exception, e:
                                print 'BANG school:'
                                print e
                                print row
                                print school_counter
                                continue

                            if has_data(row, ['contact_name']): 
                                try:
                                    clean_number = only_digits(row['phone'])
                                    clean_alt_number = only_digits(row['alternate_phone'])
                                    headmaster, created = Contact.objects.get_or_create(name=row['contact_name'],\
                                        phone=clean_number)
                                    headmaster.alternate_phone = clean_alt_number
                                    headmaster.schools.add(school)
                                    headmaster.save()

                                except Exception, e:
                                    print 'BANG headmaster:'
                                    print e
                                    print row
                                    continue

                            if has_data(row, ['number_of_pallets']):
                                try:
                                    cargo = Cargo.objects.create(commodity=commodity,\
                                                quantity=row['number_of_pallets'])

                                except Exception, e:
                                    print 'BANG cargo:'
                                    print e
                                    print row
                                    continue

                                try:
                                    origin, o_created = Facility.objects.get_or_create(location_id=country.pk,\
                                        location_type=ContentType.objects.get(model='country'))
                                    destination, d_created = Facility.objects.get_or_create(location_id=school.pk,\
                                        location_type=ContentType.objects.get(model='school'))
                                    shipment = Shipment.objects.create(status='P',\
                                       origin=origin,\
                                       destination=destination)
                                    shipment.cargos.add(cargo)

                                except Exception, e:
                                    print 'BANG shipment:'
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
