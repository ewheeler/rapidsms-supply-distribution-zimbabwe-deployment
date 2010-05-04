#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from rapidsms.contrib.handlers import KeywordHandler
from rapidsms.models import Contact


class DeliveryHandler(KeywordHandler):
    """
    """

    keyword = "delivery|del|received|receive"

    def help(self):
        self.respond("DON'T PANIC")

    def handle(self, text):

        self.respond("WORD UP!")
