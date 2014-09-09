#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Pythonic XML Security Library implementation"""

import base64
import hashlib
import lxml.etree
from cStringIO import StringIO
from M2Crypto import RSA

# Features:
#  * Uses M2Crypto and lxml (libxml2) but it is independent from libxmlsec1
#  * Sign, Verify, Encrypt & Decrypt XML documents


SIG_TMPL = """
<SignedInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
  <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315" />
  <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1" />
  <Reference URI="%(ref_uri)s">
    <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1" />
    <DigestValue>%(digest_value)s</DigestValue>
  </Reference>
</SignedInfo>
"""

SIGNED_TMPL = """
<?xml version="1.0" encoding="UTF-8"?>
<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
%(signed_info)s
<SignatureValue>%(signature_value)s</SignatureValue>
<KeyInfo>
  <KeyValue>
    <RSAKeyValue>
      <Modulus></Modulus>
      <Exponent></Exponent>
    </RSAKeyValue>
  </KeyValue>
</KeyInfo>
%(ref_xml)s
</Signature>
"""

def canonicalize(xml):
    "Return the canonical (c14n) form of the xml document for hashing"
    # UTF8, normalization of line feeds/spaces, quoting, attribute ordering...
    et = lxml.etree.parse(StringIO(xml))
    output = StringIO()
    et.write_c14n(output)
    return output.getvalue()


def digest(payload):
    "Create a SHA1 hash and return the base64 string"
    return base64.b64encode(hashlib.sha1(payload).digest())


def rsa_sign_ref(ref_xml, ref_uri, key, password=None):
    "Sign an XML document (by reference) usign RSA"

    # normalize the referenced xml (to compute the SHA1 hash)
    ref_xml = canonicalize(ref_xml)
    # create the signed xml normalized (with the referenced uri and hash value)
    signed_info = SIG_TMPL % {'ref_uri': ref_uri, 
                              'digest_value': digest(ref_xml)}
    signed_info = canonicalize(signed_info)
    # Sign the SHA1 digest of the signed xml using RSA cipher
    pkey = RSA.load_key(key, lambda *args, **kwargs: password)
    signature = pkey.sign(hashlib.sha1(signed_info).digest())
    # extract info from private key
    key_info = ""
    # create the final xml signed message
    return SIGNED_TMPL % {
            'ref_xml': ref_xml, 'ref_uri': ref_uri,
            'signed_info': signed_info,
            'signature_value': base64.b64encode(signature),
            }



if __name__ == "__main__":
    sample_xml = """<Object xmlns="http://www.w3.org/2000/09/xmldsig#" Id="object">data</Object>"""
    print canonicalize(sample_xml)
    print rsa_sign_ref(sample_xml, '#object', "private.key", "password")
