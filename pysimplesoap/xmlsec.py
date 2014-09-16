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
import os
import lxml.etree
from cStringIO import StringIO
from M2Crypto import BIO, EVP, RSA, X509, m2

# Features:
#  * Uses M2Crypto and lxml (libxml2) but it is independent from libxmlsec1
#  * Sign, Verify, Encrypt & Decrypt XML documents


SIG_TMPL = """
<SignedInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
  <CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#" />
  <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1" />
  <Reference URI="%(ref_uri)s">
    <Transforms>
      <Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#" />
    </Transforms>
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
%(key_info)s
%(ref_xml)s
</Signature>
"""

KEY_INFO_TMPL = """
<KeyInfo>
  <KeyValue>
    <RSAKeyValue>
      <Modulus>%(modulus)s</Modulus>
      <Exponent>%(exponent)s</Exponent>
    </RSAKeyValue>
  </KeyValue>
</KeyInfo>
"""

def canonicalize(xml):
    "Return the canonical (c14n) form of the xml document for hashing"
    # UTF8, normalization of line feeds/spaces, quoting, attribute ordering...
    et = lxml.etree.parse(StringIO(xml))
    output = StringIO()
    et.write_c14n(output, exclusive=True)
    return output.getvalue()


def sha1_hash_digest(payload):
    "Create a SHA1 hash and return the base64 string"
    return base64.b64encode(hashlib.sha1(payload).digest())


def rsa_sign_ref(ref_xml, ref_uri, key, password=None, key_info=None):
    "Sign an XML document (by reference) usign RSA"

    # normalize the referenced xml (to compute the SHA1 hash)
    ref_xml = canonicalize(ref_xml)
    # create the signed xml normalized (with the referenced uri and hash value)
    signed_info = SIG_TMPL % {'ref_uri': ref_uri, 
                              'digest_value': sha1_hash_digest(ref_xml)}
    signed_info = canonicalize(signed_info)
    # Sign the SHA1 digest of the signed xml using RSA cipher
    pkey = RSA.load_key(key, lambda *args, **kwargs: password)
    signature = pkey.sign(hashlib.sha1(signed_info).digest())
    # create the final xml signed message
    return {
            'ref_xml': ref_xml, 'ref_uri': ref_uri,
            'signed_info': signed_info,
            'signature_value': base64.b64encode(signature),
            'key_info': key_info or rsa_key_info(pkey),
            }


def rsa_verify(xml, signature, key):
    "Verify a XML document signature usign RSA-SHA1, return True if valid"

    # load the public key (from buffer or filename)
    if key.startswith("-----BEGIN PUBLIC KEY-----"):
        bio = BIO.MemoryBuffer(key)
        rsa = RSA.load_pub_key_bio(bio)
    else:
        rsa = RSA.load_pub_key(certificate)
    # create the digital envelope
    pubkey = EVP.PKey()
    pubkey.assign_rsa(rsa)
    # do the cryptographic validation (using the default sha1 hash digest)
    pubkey.reset_context(md='sha1')
    pubkey.verify_init()
    # normalize and feed the signed xml to be verified
    pubkey.verify_update(canonicalize(xml))
    ret = pubkey.verify_final(base64.b64decode(signature))
    return ret == 1


def rsa_key_info(pkey):
    "Convert private key (PEM) to XML Signature format (RSAKeyValue)"
    exponent = base64.b64encode(pkey.e[4:])
    modulus = m2.bn_to_hex(m2.mpi_to_bn(pkey.n)).decode("hex").encode("base64")
    return KEY_INFO_TMPL % {
        'modulus': modulus,
        'exponent': exponent,
        }


def x509_extract_rsa_public_key(cert, binary=False):
    "Return the public key (PEM format) from a X509 certificate"
    if binary:
        bio = BIO.MemoryBuffer(cert)
        x509 = X509.load_cert_bio(bio, X509.FORMAT_DER)
    elif cert.startswith("-----BEGIN CERTIFICATE-----"):
        bio = BIO.MemoryBuffer(cert)
        x509 = X509.load_cert_bio(bio, X509.FORMAT_PEM)
    else:
        x509 = X509.load_cert(cert, 1)
    return x509.get_pubkey().get_rsa().as_pem()


if __name__ == "__main__":
    sample_xml = """<Object xmlns="http://www.w3.org/2000/09/xmldsig#" Id="object">data</Object>"""
    print canonicalize(sample_xml)
    vars = rsa_sign_ref(sample_xml, '#object', "no_encriptada.key", "password")
    print SIGNED_TMPL % vars
    public_key = x509_extract_rsa_public_key(open("zunimercado.crt").read())
    assert rsa_verify(vars['signed_info'], vars['signature_value'], public_key)
