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

# Features:
#  * Uses M2Crypto and lxml (libxml2) but it is independent from libxmlsec1
#  * Sign, Verify, Encrypt & Decrypt XML documents


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


if __name__ == "__main__":
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="urn:envelope">
  <Data b='a' a='b'>
	Hello, World!
  </Data>
</Envelope>"""
    print canonicalize(sample_xml)
    