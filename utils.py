#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import operator

# http://code.google.com/p/pylevenshtein/
from Levenshtein import distance

# http://bitpim.svn.sourceforge.net/viewvc/bitpim/trunk/bitpim/src/native/strings/
from jarow import jarow

# http://mwh.geek.nz/2009/04/26/python-damerau-levenshtein-distance/
from dameraulevenshtein import dameraulevenshtein

def calc_dists(db_str, search_str):
    # find levenshtein distance
    lev = distance(db_str, search_str)
    # find damerau-levenshtein distance
    dl = dameraulevenshtein(db_str, search_str)
    # find jaro-winkler distance
    jw = jarow(db_str, search_str)
    return (lev, dl, jw)

def closest_matches(d, n=100):
    top_by_lev = None
    top_by_dl = None

    if len(d) > 0:
        # sort list by shortest levenshtein distance
        d.sort(None, operator.itemgetter(2))
        # save closest n levenshtein distances
        top_by_lev = d[:n]

        # sort list by shortest damerau-levenshtein distance
        d.sort(None, operator.itemgetter(3))
        # save closest n damerau-levenshtein distances
        top_by_dl = d[:n]

        def average(values):
            return sum(values, 0.0) / len(values)

        # calculate average levenshtein distance of n distances
        avg_lev_dist = average([x[2] for x in top_by_lev])
        # make a list of levenshtein distances that are below average
        below_lev_avg = [x for x in top_by_lev if (x[2] <= avg_lev_dist)]

        # calculate average damerau-levenshtein distance of n distances
        avg_dl_dist = average([x[3] for x in top_by_dl])
        # make a list of damerau-levenshtein distances that are below average
        below_dl_avg = [x for x in top_by_dl if (x[3] <= avg_dl_dist)]

        # make a list of jaro-winkler distances that are above 0.75
        above_75_jaro = [x for x in d if (x[4] >= 0.75)]

        # make a list of items with below avg dl and lev distances
        dl_lev = filter(lambda x:x in below_dl_avg, below_lev_avg)

        # intersect with list of items with best jw distances
        return filter(lambda x:x in above_75_jaro, dl_lev)
