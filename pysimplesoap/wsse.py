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
from .simplexml import SimpleXMLElement


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


BIN_TOKEN_TMPL = """<?xml version="1.0" encoding="UTF-8"?>
<wsse:Security soapenv:mustUnderstand="1" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
    <wsse:BinarySecurityToken EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary" ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3" wsu:Id="CertId-45851B081998E431E8132880700036719" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
%(certificate)s</wsse:BinarySecurityToken>
    <ds:Signature Id="Signature-13" xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
        %(signed_info)s
        <ds:SignatureValue>%(signature_value)s</ds:SignatureValue>
        <ds:KeyInfo Id="KeyId-45851B081998E431E8132880700036720">
            <wsse:SecurityTokenReference wsu:Id="STRId-45851B081998E431E8132880700036821" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
                <wsse:Reference URI="#CertId-45851B081998E431E8132880700036719" ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3"/>
            </wsse:SecurityTokenReference>
        </ds:KeyInfo>
    </ds:Signature>
</wsse:Security>
"""

class BinaryTokenSignature:
    "WebService Security extension to add a basic signature to xml request"

    def __init__(self, certificate="", private_key="", password=None):
        # read the X509v3 certificate (PEM)
        self.certificate = ''.join([line for line in open(certificate)
                                         if not line.startswith("---")])
        self.private_key = private_key
        self.password = None

    def preprocess(self, client, request, method, args, kwargs, headers, soap_uri):
        # get xml elements:
        body = request('Body', ns=soap_uri, )
        header = request('Header', ns=soap_uri, )
        # prepare body xml attributes to be signed (reference)
        body['wsu:Id'] = "id-14"
        body['xmlns:wsu'] = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
        ref_xml = body.as_xml()
        # sign using RSA-SHA1 (XML Security)
        from . import xmlsec
        vars = xmlsec.rsa_sign_ref(ref_xml, "#id-14", 
                                   self.private_key, self.password)
        vars['certificate'] = self.certificate
        # generate the xml (filling the placeholders)
        wsse = SimpleXMLElement(BIN_TOKEN_TMPL % vars)
        header.import_node(wsse)
