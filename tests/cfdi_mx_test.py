#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Mexico SAT (IRS) Electronic Invoice (Comprobantes Fiscales Digitales)"""

from decimal import Decimal
import os
import unittest
from pysimplesoap.client import SoapClient, SoapFault

import sys
if sys.version > '3':
    basestring = str
    long = int


class TestCFDI(unittest.TestCase):

    def test_obtener_token(self):
            
        # Concetarse al webservice (en producción, ver cache y otros parametros):
        WSDL = "http://pruebas.ecodex.com.mx:2044/ServicioSeguridad.svc?wsdl"
        client = SoapClient(wsdl=WSDL, ns="ns0", soap_ns="soapenv")

        # llamo al método remoto:
        retval = client.ObtenerToken(RFC="AAA010101AAA", TransaccionID=1234)
        # muestro los resultados:
        self.assertIsInstance(retval['Token'], basestring)
        self.assertIsInstance(retval['TransaccionID'], long)
 
    def test_cancela(self):
            
        # Concetarse al webservice (en producción, ver cache y otros parametros):
        WSDL = "https://pruebas.ecodex.com.mx:2045/ServicioCancelacion.svc?wsdl"
        client = SoapClient(wsdl=WSDL, ns="cfdi", soap_ns="soapenv")
  
        try:
            r  = client.CancelaMultiple(
                    ListaCancelar=[{"guid": "abcdabcd-abcd-abcd-acbd-abcdabcdabcd"}], 
                    RFC="AAA010101AAA", 
                    Token="62cb344df85acab90c3a68174ed5e452b3c50b2a", 
                    TransaccionID=1234)
        except SoapFault as sf:
            self.assertIn("El Token no es valido o ya expiro", str(sf.faultstring))
            
        ##for res in r['Resultado']:
        ##    rc = res['ResultadoCancelacion']
        ##    print rc['UUID'], rc['Estatus']
        ##    print res['TransaccionID']
            
    def test_timbrado(self):
        # this tests "infinite recursion" issues
        
        # Concetarse al webservice (en producción, ver cache y otros parametros):
        WSDL = "https://digitalinvoicecfdi.com.mx/WS_WSDI/DigitalInvoice.WebServices.WSDI.Timbrado.svc?wsdl"
        #WSDL = "federico.wsdl"
        client = SoapClient(wsdl=WSDL, ns="ns0", soap_ns="soapenv")

        # llamo al método remoto:
        try:
            retval = client.TimbrarTest(comprobanteBytesZipped="1234")
        except SoapFault as sf:
            self.assertIn("verifying security for the message", str(sf.faultstring))

        # muestro los resultados:
        ##print retval['TimbrarTestResult']

