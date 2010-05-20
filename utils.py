#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re
import operator

# http://code.google.com/p/pylevenshtein/
from Levenshtein import distance

# http://bitpim.svn.sourceforge.net/viewvc/bitpim/trunk/bitpim/src/native/strings/
from jarow import jarow

# http://mwh.geek.nz/2009/04/26/python-damerau-levenshtein-distance/
from dameraulevenshtein import dameraulevenshtein

def calc_dists(mine, theirs):
    ''' Calculates Levenshtein distance, Damerau-Levenshtein distance,
        and Jaro-Winkler distance between two strings.

        Returns a 3-item tuple containing results, respectively.
    '''
    my_str = unicode(mine)
    search_str = unicode(theirs)
    # find levenshtein distance
    lev = distance(my_str, search_str)
    # find damerau-levenshtein distance
    dl = dameraulevenshtein(my_str, search_str)
    # find jaro-winkler distance
    jw = jarow(my_str, search_str)
    return (lev, dl, jw)

def closest_matches(d, n=100):
    ''' Expects a list of tuples (d) conisisting of:
        (
            'search string used for distance calculations',
            object whose field is being compared to search string,
            levenshtein distance,
            damerau-levenshtein distance,
            jaro-winkler distance
        )

        Returns a subset of this list (in the same format)
        containing the closest matches.
    '''
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
        best_matches = filter(lambda x:x in above_75_jaro, dl_lev)

        # see if we have any perfect matches
        perfect_matches = [x for x in best_matches if (x[2]==0 and x[3]==0 and x[4]==1.0)]

        if len(perfect_matches) > 0:
            return perfect_matches
        else:
            return best_matches

def check_tokens(token_labels, token_isdigit_exp, submission):
    #token_labels = ['surname', 'facility_code', 'facility_name']
    #token_isdigit_exp = ['False', 'True', 'False']

    #token_data = ['van', 'wheeler', '99', 'unicef', 'house']
    #token_isdigit_act = ['False', 'False', 'True', 'False', 'False'] 

    if len(token_data) < len(token_labels):
        print ('NOT ENOUGH TOKENS')

    def merge_leading():
        for e, expected in enumerate(token_isdigit_exp):
            for a, actual in enumerate(token_isdigit_act):
                if expected is True and actual is False:
                    if a == e:
                        continue
                if expected and actual is False:
                    if e == a:
                        break
                if expected and actual is True:
                    if a > 0 and e <= a:
                        print '*** merging leading ***'
                        leading_tokens = token_data[:a]
                        new_lead = " ".join(leading_tokens)
                        del token_data[:a]
                        token_data.insert(0, new_lead)
                        print token_data
                        return

    def merge_trailing():
        for e, expected in enumerate(token_isdigit_exp):
            for a, actual in enumerate(token_isdigit_act):
                if expected is True and actual is False:
                    if a == e:
                        continue
                if expected and actual is True:
                    if e == a:
                        break
                if expected and actual is False:
                    next_digit = None
                    for d, digits in enumerate(token_isdigit_act):
                        if d > a:
                            if digits:
                                next_digit = d
                                break
                    if e < a:
                        print '*** merging trailing ***'
                        print expected
                        print actual
                        print next_digit
                        trailing_tokens = token_data[a:next_digit]
                        print trailing_tokens
                        new_trail = " ".join(trailing_tokens)
                        print new_trail
                        del token_data[a:next_digit]
                        token_data.insert(a, new_trail)
                        print token_data
                        break
                
    token_data = submission.split()
    print token_data
    if len(token_data) > len(token_labels):
        print ('TOO MANY TOKENS')
        token_isdigit_act = [t.isdigit() for t in token_data]
        merge_leading()
        token_isdigit_act = [t.isdigit() for t in token_data]
        merge_trailing()


    return token_data
