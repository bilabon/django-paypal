#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
from time import sleep

from paypal.standard.ipn.signals import invalid_ipn_received, valid_ipn_received
from paypal.standard.models import PayPalStandardBase


class PayPalIPN(PayPalStandardBase):
    """Logs PayPal IPN interactions."""
    format = u"<IPN: %s %s>"

    class Meta:
        db_table = "paypal_ipn"
        verbose_name = "PayPal IPN"

    def _postback(self):
        """Perform PayPal Postback validation."""
        # handling "Fatal Failure" PayPal's response by revalidating
        # attempts_number times
        # PayPal's response: <html><body>Fatal Failure <br></body></html>
        attempts_number = 5
        wait_seconds = 2
        content = b""
        while attempts_number > 0:
            data = b"cmd=_notify-validate&" + self.query.encode("ascii")
            content = requests.post(self.get_endpoint(), data=data).content
            if content not in [b"INVALID", b"VERIFIED"]:
                attempts_number -= 1
                sleep(wait_seconds)
            else:
                attempts_number = 0
        return content

    def _verify_postback(self):
        if self.response != "VERIFIED":
            self.set_flag("Invalid postback. ({0})".format(self.response))

    def send_signals(self):
        """Shout for the world to hear whether a txn was successful."""
        if self.flag:
            invalid_ipn_received.send(sender=self)
            return
        else:
            valid_ipn_received.send(sender=self)

    def __repr__(self):
        return '<PayPalIPN id:{0}>'.format(self.id)

    def __str__(self):
        return "PayPalIPN: {0}".format(self.id)
