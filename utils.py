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

def split_into_tokens(expected_tokens, submission):

    type_tokens_exp = [item for sublist in [x.values() for x in expected_tokens] for item in sublist]
    tokens_labels = [item for sublist in [x.keys() for x in expected_tokens] for item in sublist]

    tokens_act = re.findall('\W+', submisison)

    num_tokens_act = re.findall('\d+', submission)
    print num_tokens_act
    if type_tokens_exp.count(True) > len(num_tokens_act):
        print 'missing num token'
    if type_tokens_exp.count(True) < len(num_tokens_act):
        print 'extra num token'

    word_tokens_act = [w.strip() for w in re.findall('\D+', submission) if w not in ['.', ' ', '']]
    print word_tokens_act
    if type_tokens_exp.count(False) > len(word_tokens_act):
        print 'missing word token'
    if type_tokens_exp.count(False) < len(word_tokens_act):
        print 'extra word token'

    tokens_data = []
    for digit in type_tokens_exp:
        if digit:
            tokens_data.append(num_tokens_act.pop(0))
        else:
            tokens_data.append(word_tokens_act.pop(0))
    
    return dict(zip(tokens_labels, tokens_data))
