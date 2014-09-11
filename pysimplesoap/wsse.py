#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Pythonic simple SOAP Client plugins for WebService Security extensions"""


from __future__ import unicode_literals
import sys
if sys.version > '3':
    basestring = unicode = str

import datetime
from decimal import Decimal
import os
import logging
import hashlib
import warnings

from . import __author__, __copyright__, __license__, __version__


class UsernameToken:
    "WebService Security extension to add a basic credentials to xml request"

    def __init__(self, username="", password=""):
        self.token = {
            'wsse:UsernameToken': {
                'wsse:Username': username,
                'wsse:Password': password,
                }
            }

    def preprocess(self, client, request, method, args, kwargs, headers, soap_uri):
        # always extract WS Security header and send it
        header = request('Header', ns=soap_uri, )
        k = 'wsse:Security'
        # for backward compatibility, use header if given:
        if k in headers:
            self.token = headers[k]
        # convert the token to xml
        header.marshall(k, self.token, ns=False, add_children_ns=False)
        #TODO: namespaces too hardwired, clean-up...
        header(k)['xmlns:wsse'] = 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd'
        #<wsse:UsernameToken xmlns:wsu='http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd'>

