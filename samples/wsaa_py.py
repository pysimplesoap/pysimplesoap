#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Example to get Autorization Ticket (WSAA webservice) - Aduana Paraguay"

# Inspired on wsaa-client.php from DvSHyS/DiOPIN/AFIP (Argentina) - 13-apr-07

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2008-2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "2.08a"

import hashlib, datetime, email, os, sys, time, traceback
from pysimplesoap.client import SoapClient, SimpleXMLElement
from pysimplesoap import xmlsec
from M2Crypto import BIO, Rand, SMIME, SSL          # openssl binding

# Constants
CERT = "pbbox.crt"          # X.509 certificate (in PEM format)
PRIVATEKEY = "pbbox.key"    # RSA private key (in PEM format)
PASSPHRASE = "xxxxxxx"      # private key password (if any)

# Webservice URL (test: homologacion):
WSDL = {'test': "https://secure.aduana.gov.py/test/wsaa/server?wsdl",
        'prod': "https://secure.aduana.gov.py/wsaaserver/Server?wsdl"}

# Remote webserver certificate validation, needed for "secure channel" spec
CACERT = None  # WSAA CA Cert (Autoridades de Confiaza)

DEFAULT_TTL = 60*60*5       # five hours
TIMEOUT = 60                # 60 seconds for http connection timeout
DEBUG = True


def create_tra(service=None, ttl=2400, cert=None):
    "Create a Access Request Ticket (TRA)"
    # Base TRA squeleton (Ticket de Requerimiento de Acceso)
    tra = SimpleXMLElement(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<loginTicketRequest version="1.0">'
        '</loginTicketRequest>')
    tra.add_child('header')
    # get the source from the certificate subject, ie "CN=empresa, O=dna, C=py"
    if cert:
        crt = xmlsec.x509_parse_cert(cert)
        tra.header.add_child('source', crt.get_subject().as_text())
    tra.header.add_child('destination', 'C=py, O=dna, OU=sofia, CN=wsaatest')
    d = int(time.mktime(datetime.datetime.now().timetuple()))
    tra.header.add_child('uniqueId', str(d))
    date = lambda ts: datetime.datetime.fromtimestamp(ts).isoformat()
    tra.header.add_child('generationTime', str(date(d-ttl)))
    tra.header.add_child('expirationTime', str(date(d+ttl)))
    tra.add_child('service', service)
    return tra.as_xml()


def sign_tra(tra,cert=CERT,privatekey=PRIVATEKEY,passphrase=""):
    "Sign using PKCS#7 the TRA and return CMS (trimming SMIME headers)"

    # Sign the text (tra) using m2crypto (openssl bindings for python)
    buf = BIO.MemoryBuffer(tra)             # create the buffer from the file
    #Rand.load_file('randpool.dat', -1)     # seed the PRNG
    s = SMIME.SMIME()                       # instantiate the SMIME
    # support encription passwords (for private key, optional)
    callback = lambda *args, **kwarg: passphrase
    # load the private key and certificate
    s.load_key(privatekey, cert, callback)      # (frmo file)
    p7 = s.sign(buf,0)                      # Sign the buffer
    out = BIO.MemoryBuffer()                # Instantiathe the output buffer 
    s.write(out, p7)                        # Generate p7 in mail format
    #Rand.save_file('randpool.dat')         # Store the PRNG's state

    # extract the message body (signed part)
    msg = email.message_from_string(out.read())
    for part in msg.walk():
        filename = part.get_filename()
        if filename == "smime.p7m":                 # is the signed part?
            return part.get_payload(decode=False)   # return the CMS


def call_wsaa(cms, wsdl=WSDL, proxy=None, cache=None, wrapper="", trace=False):
    "Call the RPC method with the CMS to get the authorization ticket (TA)"

    # create the webservice client
    client = SoapClient(
        location = wsdl[:-5], #location, use wsdl,
        cache = cache,
        #proxy = parse_proxy(proxy),
        #cacert = cacert,
        timeout = TIMEOUT,
        ns = "ejb", 
        # TODO: find a better method to not include ns prefix in children:
        #   (wsdl parse should detect qualification instead of server dialect)
        soap_server = "jetty",  
        namespace = "http://ejb.server.wsaa.dna.gov.py/",
        soap_ns = "soapenv",
        trace = trace)
    # fix the wrong location (192.4.1.39:8180 in the WDSL)
    ##ws = client.services['WsaaServerBeanService']
    ##location = ws['ports']['WsaaServerBeanPort']['location']
    ##location = location.replace("192.4.1.39:8180", "secure.aduana.gov.py")
    ##ws['ports']['WsaaServerBeanPort']['location'] = wsdl[:-5] #location
    
    # call the remote method
    try:
        results = client.loginCms(arg0=str(cms))
    except:
        # save sent and received messages for debugging:
        open("request.xml", "w").write(client.xml_request)
        open("response.xml", "w").write(client.xml_response)
        raise
    
    # extract the result:
    ta = results['return'].encode("utf-8")
    return ta


if __name__=="__main__":
    
    tra = create_tra(service="test", ttl=DEFAULT_TTL, cert=CERT)
    print tra
    cms = sign_tra(tra, CERT, PRIVATEKEY)
    ta = call_wsaa(cms, WSDL['test'], trace=True)
    print ta

