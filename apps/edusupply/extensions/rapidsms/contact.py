#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.db import models
from rapidsms.contrib.locations.models import Location

import utils

from metaphone import dm
from jarow import jarow

class HeadmasterOrDEO(models.Model):
    phone = models.CharField(max_length=160, blank=True, null=True)
    alternate_phone = models.CharField(max_length=160, blank=True, null=True)
    facilities = models.ManyToManyField(Location, related_name='facilitycontact', blank=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def closest_by_name(klass, search_string, n=100):
        d = []

        for obj in klass.objects.all():
            args = [str(obj.name).upper(), search_string.upper()]
            # also calculate distance between search_string and 
            # the best guess of a surname (longest word in name)
            name_list = str(obj.name).upper().replace('.', ' ').split()
            surname_guess = max(name_list, key=len) 

            alt_args = [surname_guess, search_string.upper()]

            args_dists = utils.calc_dists(*args)
            alt_dists = utils.calc_dists(*alt_args)

            # use the shortest of these distances
            d.append((search_string, obj,\
                min([args_dists[0], alt_dists[0]]),\
                min([args_dists[1], alt_dists[1]]),\
                max([args_dists[2], alt_dists[2]])))

        return utils.closest_matches(d, n)

    @classmethod
    def closest_by_sound(klass, search_string, similarity_threshold = 0.8):
        same = []
        similar = []

        # metaphones of search term
        search_sound = dm(search_string)

        for obj in klass.objects.all():
            name_list = str(obj.name).upper().replace('.', ' ').split()
            surname_guess = max(name_list, key=len) 

            # metaphones of obj name
            obj_sound = dm(surname_guess)

            if search_sound[0] == obj_sound[0]:
                # primary metaphones match exactly
                same.append((obj, obj_sound, 1.0))
            else:
                # no exact match, so see if the primary metaphones are similar
                primary_sound_dist = jarow(str(search_sound[0]), str(obj_sound[0]))
                if primary_sound_dist >= similarity_threshold:
                    similar.append((obj, obj_sound, primary_sound_dist))

                elif search_sound[1] is not None:
                    # still dont have a good match. see if secondary metaphone
                    # of obj name is similar to the search_sound
                    secondary_sound_dist = jarow(str(search_sound[0]), str(obj_sound[1]))
                    if secondary_sound_dist >= similarity_threshold:
                        similar.append((obj, obj_sound, secondary_sound_dist))

                else:
                    continue

        if len(same) > 0:
            return search_sound, same
        else:
            # return similar sounding matches if there are no exact matches
            return search_sound, similar
