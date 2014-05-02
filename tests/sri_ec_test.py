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

"""Ecuador S.R.I. Electronic Invoice (Emisión de Documentos Electrónicos)"""

from __future__ import unicode_literals

from decimal import Decimal
import os
import unittest
from pysimplesoap.client import SoapClient, SoapFault

import sys
if sys.version > '3':
    basestring = str
    long = int

# Documentation: http://www.sri.gob.ec/web/10138/145


class TestSRI(unittest.TestCase):
 
    def test_validar(self):
        "Prueba de envío de un comprovante electrónico"
        WSDL = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
        # https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl
        client = SoapClient(wsdl=WSDL, ns="ec")
        ret = client.validarComprobante(xml="cid:1218403525359")
        self.assertEquals(ret, {'RespuestaRecepcionComprobante': {'comprobantes': [{'comprobante': {'mensajes': [{'mensaje': {'identificador': '35', 'mensaje': 'ARCHIVO NO CUMPLE ESTRUCTURA XML', 'informacionAdicional': 'Content is not allowed in prolog.', 'tipo': 'ERROR'}}], 'claveAcceso': 'N/A'}}], 'estado': 'DEVUELTA'}})
            

    def test_autorizar(self):
            
        WSDL = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'
        # https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl
        client = SoapClient(wsdl=WSDL, ns="ec")
        ret = client.autorizacionComprobante(claveAccesoComprobante="1702201205176001321000110010030001000011234567816")
        self.assertEquals(ret, {'RespuestaAutorizacionComprobante': {'autorizaciones': [], 'claveAccesoConsultada': '1702201205176001321000110010030001000011234567816', 'numeroComprobantes': '0'}})

