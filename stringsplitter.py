#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re

patterns = [
    ('number', re.compile('\d+')),
    #('float', re.compile('\d*\.?\d*')),
    ('bool', re.compile('yes|y|yeah|oui|o|true|t|no|n|nope|non|false|f')), 
    ('word', re.compile('\w+')),
    ('.', re.compile(r'\.')),
    (',', re.compile(r'\,')),
]
whitespace = re.compile('\W+')

def tokenize(string):
    while string:

        # strip off whitespace
        m = whitespace.match(string)
        if m:
            string = string[m.end():]

        for tokentype, pattern in patterns:
            m = pattern.match(string)
            if m:
                yield tokentype, m.group(0)
                string = string[m.end():]

def parseNumber(tokens):
    print 'PARSING NUMBER'
    tokentype, literal = tokens.pop(0)
    print tokentype
    print literal
    assert tokentype == 'number'
    return literal

def parseFloat(tokens):
    print 'PARSING FLOAT'
    float_str = parseNumber(tokens)
    print float_str
    while tokens and tokens[0][0] in ('.', ',', 'number'):
        tokentype, literal = tokens.pop(0)
        if tokentype in ('.', ',', 'number'):
            float_str = float_str + literal
        else:
            raise ValueError("Parse Error, unexpected %s %s" % (tokentype, literal))
    print float_str
    return float_str

def parseWord(tokens):
    print 'PARSING WORD'
    tokentype, literal = tokens.pop(0)
    print tokentype
    print literal
    assert tokentype == 'word'
    return literal

def parseWords(tokens):
    print 'PARSING WORDS'
    words = parseWord(tokens)
    print words
    while tokens and tokens[0][0] == 'word':
        tokentype, literal = tokens.pop(0)
        if tokentype == 'word':
            words = words + ' ' + literal
        else:
            raise ValueError("Parse Error, unexpected %s %s" % (tokentype, literal))
    print words
    return words
    
def parse(expected_types, labels, tokens):
    tokenlist = list(tokens)
    tokens = [] 
    def consume_tokenlist():
        for type in expected_types:
            if type == 'number':
                yield parseNumber(tokenlist)
            elif type == 'words':
                yield parseWords(tokenlist)
            elif type == 'word':
                yield parseWord(tokenlist)
            else:
                print 'Unknown tokentype'
                yield 'None'

    consumer = consume_tokenlist()
    for label in labels:
        try:
            token = consumer.next()
            print token
            tokens.append((label,token))
        except StopIteration:
            break

    if tokenlist:
        print 'Unconsumed data', tokenlist
        return tokens, tokenlist
    return tokens 

def parse_into_tokens(expected_tokentypes, labels, string):
    return parse(expected_tokentypes, labels, tokenize(string))
