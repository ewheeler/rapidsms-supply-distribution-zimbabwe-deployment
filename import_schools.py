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

from logistics.models import Campaign
from logistics.models import Commodity
from logistics.models import Cargo
from logistics.models import Shipment
from logistics.models import Facility

def import_csv(args):

    # use codecs.open() instead of open() so all characters are utf-8 encoded
    # BEFORE we start dealing with them (just in case)
    # rU option is for universal-newline mode which takes care of \n or \r etc
    csvee = codecs.open("all_schools.csv", "rU", encoding='utf-8', errors='ignore')

    # sniffer attempts to guess the file's dialect e.g., excel, etc
    #dialect = csv.Sniffer().sniff(csvee.read(1024))
    dialect = csv.excel_tab

    # for some reason, sniffer was finding '"'
    #dialect.quotechar = '"'
    csvee.seek(0)

    # DictReader uses first row of csv as key for data in corresponding column
    reader = csv.DictReader(csvee, dialect=dialect, delimiter=",",\
        quoting=csv.QUOTE_ALL, doublequote=True)

    try:
        country, c_created = Country.objects.get_or_create(name="Zimbabwe",\
            slug=slugify("Zimbabwe"))

        #TODO calculate per-pallet weight
        commodity, c_created = Commodity.objects.get_or_create(name="Textbooks",\
            slug="textbooks", unit="KT", aliases="textbook,books,book")

        campaign, created = Campaign.objects.get_or_create(name="Primary School Textbooks")
        campaign.commodities.add(commodity)

        satellite_counter = 0
        school_counter = 0
    except Exception, e:
        print 'BANG initial objects'
        print e

    try:
        print 'begin rows'
        '''
        No,
        School name,
        Km. Distance DEO to school,
        Contact Name,
        Telephone,
        Alternative phone number,
        School address,
        school code,
        GPS SOUTH,
        GPS EAST,
        DEO,
        PHONE,
        Province Name,
        District Code,
        District Name,
        School Type,
        FormNo.,
        PrimSec,
        Total enrollment,
        ROUND I Kits per school,
        ROUND I Actual kits,
        ROUND I delivery group#,
        Delivered by,
        ROUND I DATE OF DELIVERY,
        ROUND I Dispatched,
        ROUND I Delivered,
        ROUND I Confirmed,
        ROUND I Comments,
        ROUND II delivery group#,
        Delivered by,
        ROUNDII DELIVERY DATE,
        ROUND II Dispatched,
        ROUND II Delivered,
        ROUND II Confirmed,
        ROUND II Comments,
        ROUND III delivery group#,
        Delivered by,
        ROUND III DELIVERY DATE,
        ROUND III Dispatched,
        ROUND III Delivered,
        ROUND III Confirmed,
        ROUND III Comments,,,,,
        '''
        row_count = 0
        for row in reader:
            row_count += 1
            if row_count % 400 == 0:
                print row_count

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

            def get_good_date(date, delimiter=False):
                # TODO parameter to choose formating
                # e.g., DDMMYY vs YYMMDD etc
#                print 'getting good date...'
#                print date
                delimiters = r"[./\\-]+"
                if delimiter:
                    # expecting DDMMYY
                    Allsect=re.split(delimiters,date)            
                else:
#                    print 'no delimiter'
                    if len(date) == 6:
                        # assume DDMMYY
                        Allsect = [date[:2], date[2:4], date[4:]] 
                    elif len(date) == 8:
                        # assume DDMMYYYY
                        Allsect = [date[:2], date[2:4], date[4:]]
                    elif len(date) == 4:
                        # assume DMYY
                        Allsect = [date[0], date[1], date[2:]]
                    elif len(date) == 5:
                        # reject ambiguous dates
                        return None, None
                        #if int(date[:2]) > 31 and (0 < int(date[2]) >= 12):
                        #    Allsect = [date[:2], date[2], date[2:]]
                        #if int(date[0]) <= 12 and (0 < int(date[1:3]) <= 31): 
                        #    Allsect = [date[0], date[1:3], date[2:]]
                    else:
                        return None, None

                if Allsect is not None:
#                    print Allsect
                    year = Allsect[2]
                    month = Allsect[1]
                    day = Allsect[0]
#                    print 'year ' + str(year)
#                    print 'month ' + str(month)
#                    print 'day ' + str(day)

                    # make sure we have a REAL day
                    if month.isdigit():
                        if int(month) == 2:
                            if int(day) > 28:
                                day = 28
                        if int(month) in [4, 6, 9, 11]:
                            if int(day) > 30:
                                day = 30
                    else:
                        return None, None

                    # if there are letters in the date, give up
                    if not year.isdigit():
                        return None, None
                    if not day.isdigit():
                        return None, None

                    # add leading digits if they are missing
                    # TODO can we use datetime.strptime for this?
                    if len(year) < 4 : 
                        year = "20%s" % year        
                    if len(month) < 2:
                        month = "0%s" % month
                    if len(day) < 2:
                        day = "0%s" % day         

#                    print 'year ' + str(year)
#                    print 'month ' + str(month)
#                    print 'day ' + str(day)
                    # return ISO string for human consumption;
                    # datetime.date for django consumption
                    good_date_str = "%s-%s-%s" % (year,month,day )
#                    print good_date_str
                    good_date_obj = datetime.date(int(year), int(month), int(day))
#                    print good_date_obj
                    return good_date_str, good_date_obj

            if has_datum(row, 'ProvName'):
                province, created = Province.objects.get_or_create(\
                    name=row['ProvName'], slug=slugify(row['ProvName']),\
                    parent_id=country.pk, parent_type=ContentType.objects.get(model='country'))

                if has_data(row, ['DistName', 'DistCode']):
                    raw_dist_code = row['DistCode']
                    clean_dist_code = None
                    try:
                        clean_dist_code = int(raw_dist_code)
                    except:
                        pass
                    district, created = District.objects.get_or_create(name=row['DistName'],\
                        slug=slugify(row['DistName']),\
                        parent_id=province.pk, parent_type=ContentType.objects.get(model='province'))
                    if clean_dist_code is not None:
                        district.code = clean_dist_code
                        district.save()

                    if has_data(row, ['deo', 'deo_phone']):
                        try:
                            clean_phone_number = only_digits(row['deo_phone'])
                            deo, created = Contact.objects.get_or_create(name=row['deo'],\
                                    phone=clean_phone_number)
                            deo.districts.add(district)
                            deo.save()

                        except Exception, e:
                            print 'BANG deo:'
                            print e
                            print row
                            print row_count
                            continue

                        def clean_and_convert_dm(raw_str):
                            str = raw_str
                            if str in ['0', ' ', '']:
                                return None
                            whitespace = re.compile("(\s+)")
                            clean_str = re.sub(whitespace, " ", str)

                            # split degree and minute.decimal, remove minute mark (')
                            clean_dm = [x.strip('\'') for x in clean_str.split()]
                            # convert degree minute.decimal to degree.decimal
                            clean_dd = dd.dm2decimal(*clean_dm)
                            return clean_dd 

                        if has_data(row, ['GPS_south', 'GPS_east']):
                            try:
                                # latitude coordinates from excel file are 
                                # all 'south' so degrees should be negative 
                                clean_GPS_south = clean_and_convert_dm(row['GPS_south']).copy_negate()
                                # longitude coordinates from excel file are
                                # all 'east' so degrees should remain positive
                                clean_GPS_east = clean_and_convert_dm(row['GPS_east'])
                            except Exception, e:
                                print 'BANG clean gps:'
                                print e
                                print row
                                print row_count
                                continue
                            try:
                                if clean_GPS_south and clean_GPS_east is not None:
                                    point, created = Point.objects.get_or_create(latitude=clean_GPS_south,\
                                                longitude=clean_GPS_east)

                            except Exception, e:
                                print 'BANG point:'
                                print e
                                print row
                                print row_count
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

                            level = row['PrimSec']
                            clean_level = 'U'
                            if level == 'Primary':
                                clean_level = 'P'
                            if level == 'Secondary':
                                clean_level = 'S'
                                    
                            clean_enrollment = only_digits(row['total_enrollment'])
                            if clean_enrollment in ["NIL", ""]:
                                clean_enrollment = None

                            clean_km_to_DEO = only_digits(row['km_to_DEO'])
                            if clean_km_to_DEO in ["NIL", ""]:
                                clean_km_to_DEO = None

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
                                    parent_id=district.pk, parent_type=ContentType.objects.get(model='district'),\
                                    level=clean_level, form_number=row['form_number'], total_enrollment=clean_enrollment)
                                school_counter += 1

                            except Exception, e:
                                print 'BANG school:'
                                print e
                                print row
                                print row_count
                                continue

                            if has_data(row, ['contact_name']): 
                                try:
                                    clean_number = only_digits(row['phone_number'])
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
                                    print row_count
                                    continue

                            try:
                                cargo = Cargo.objects.create(commodity=commodity)

                            except Exception, e:
                                print 'BANG cargo:'
                                print e
                                print row
                                print row_count
                                continue


                            try:
                                origin, o_created = Facility.objects.get_or_create(location_id=country.pk,\
                                    location_type=ContentType.objects.get(model='country'))
                                destination, d_created = Facility.objects.get_or_create(location_id=school.pk,\
                                    location_type=ContentType.objects.get(model='school'))

                                shipment = Shipment(status='P', origin=origin,\
                                    destination=destination)

                                shipment.save()

                                shipment.cargos.add(cargo)
                                campaign.shipments.add(shipment)

                            except Exception, e:
                                print 'BANG shipment:'
                                print e
                                print row
                                print row_count
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
