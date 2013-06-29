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

"Argentina AFIP (IRS) Electronic Invoice & Currency Exchange Control"

from decimal import Decimal
import os
import unittest
import sys
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper
from dummy_utils import DummyHTTP, TEST_DIR

TRACE= False

WSDLs=[
    "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl",
    "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl",
    "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
    "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL",
    "https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl",
    "https://serviciosjava.afip.gob.ar/wsmtxca/services/MTXCAService?wsdl",
    "https://wswhomo.afip.gov.ar/wsfexv1/service.asmx?WSDL",
    "https://servicios1.afip.gov.ar/wsfexv1/service.asmx?WSDL",
    ]

wrapper = None
cache = "./cache"
proxy_dict = None
cacert = None

class TestIssues(unittest.TestCase):
   
    def atest_wsaa_exception(self):
        "Test WSAA for SoapFault"
        WSDL = "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl"
        client = SoapClient(wsdl=WSDL, ns="web", trace=False)
        try:
            resultado = client.loginCms('31867063')
        except SoapFault, e:
            self.assertEqual(e.faultcode, 'ns1:cms.bad')

        try:
            resultado = client.loginCms(in0='31867063')
        except SoapFault, e:
            self.assertEqual(e.faultcode, 'ns1:cms.bad')

    def test_wsfev1_dummy(self):
        "Test Argentina AFIP Electronic Invoice WSFEv1 dummy method"
        client = SoapClient(
            wsdl="https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
            trace=TRACE, cache=None,
            )
        result = client.FEDummy()['FEDummyResult']
        self.assertEqual(result['AppServer'], "OK")
        self.assertEqual(result['DbServer'], "OK")
        self.assertEqual(result['AuthServer'], "OK")

    def test_wsfexv1_dummy(self):
        "Test Argentina AFIP Electronic Invoice WSFEXv1 dummy method"
        client = SoapClient(
            wsdl="https://wswhomo.afip.gov.ar/wsfexv1/service.asmx?WSDL",
            trace=TRACE, cache=None,
            )
        result = client.FEXDummy()['FEXDummyResult']
        self.assertEqual(result['AppServer'], "OK")
        self.assertEqual(result['DbServer'], "OK")
        self.assertEqual(result['AuthServer'], "OK")

    def test_wsbfe_dummy(self):
        "Test Argentina AFIP Electronic Invoice WSBFE dummy method"
        client = SoapClient(
            wsdl="https://wswhomo.afip.gov.ar/wsbfe/service.asmx?WSDL",
            trace=TRACE, cache=None,
            )
        result = client.BFEDummy()['BFEDummyResult']
        self.assertEqual(result['AppServer'], "OK")
        self.assertEqual(result['DbServer'], "OK")
        self.assertEqual(result['AuthServer'], "OK")

    def test_wsmtxca_dummy(self):
        "Test Argentina AFIP Electronic Invoice WSMTXCA dummy method"
        client = SoapClient(
            wsdl="https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl",
            trace=TRACE, cache=None, ns='ser',
            )
        result = client.dummy()
        self.assertEqual(result['appserver'], "OK")
        self.assertEqual(result['dbserver'], "OK")
        self.assertEqual(result['authserver'], "OK")

    def test_wscoc_dummy(self):
        "Test Argentina AFIP Foreign Exchange Control WSCOC dummy method"
        client = SoapClient(
            wsdl="https://fwshomo.afip.gov.ar/wscoc/COCService?wsdl",
            trace=TRACE, cache=None, ns='ser',
            )
        result = client.dummy()['dummyReturn']
        self.assertEqual(result['appserver'], "OK")
        self.assertEqual(result['dbserver'], "OK")
        self.assertEqual(result['authserver'], "OK")


    def test_wsfexv1_getcmp(self):
        "Test Argentina AFIP Electronic Invoice WSFEXv1 GetCMP method"
        # create the proxy and parse the WSDL
        client = SoapClient(
            wsdl="https://wswhomo.afip.gov.ar/wsfexv1/service.asmx?WSDL",
            trace=TRACE, cache=None,
            )
        # load saved xml
        xml = open(os.path.join(TEST_DIR, "wsfexv1_getcmp.xml")).read()
        client.http = DummyHTTP(xml)
        # call RPC
        ret = client.FEXGetCMP(
            Auth={'Token': "", 'Sign': "", 'Cuit': ""},
            Cmp={
                'Cbte_tipo': "19",
                'Punto_vta': "3",
                'Cbte_nro': "38",
            })
        # analyze result
        result = ret['FEXGetCMPResult']
        self.assertEqual(result['FEXErr']['ErrCode'], 0)
        self.assertEqual(result['FEXErr']['ErrMsg'], 'OK')
        self.assertEqual(result['FEXEvents']['EventCode'], 0)
        resultget = result['FEXResultGet']
        self.assertEqual(resultget['Obs'], None)
        self.assertEqual(resultget['Cae'], '61473001385110')
        self.assertEqual(resultget['Fch_venc_Cae'], '20111202')
        self.assertEqual(resultget['Fecha_cbte'], '20111122')
        self.assertEqual(resultget['Punto_vta'], 3)
        self.assertEqual(resultget['Resultado'], "A")
        self.assertEqual(resultget['Cbte_nro'], 38)
        self.assertEqual(resultget['Imp_total'], Decimal('130.21'))

