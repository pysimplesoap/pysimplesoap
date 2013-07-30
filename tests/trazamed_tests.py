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

"Argentina National Medical Drug Traceability Program (ANMAT - PAMI - INSSJP)"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"

import datetime
import os
import unittest
import sys
import time

from pysimplesoap.client import SoapClient, SoapFault, parse_proxy, \
                                set_http_wrapper

HOMO = False

WSDL = "https://186.153.145.2:9050/trazamed.WebService?wsdl"
       #https://186.153.145.2:9050/trazamed.WebService?wsdl
LOCATION = "https://186.153.145.2:9050/trazamed.WebService"
#WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService?wsdl"


class TestTrazamed(unittest.TestCase):

    def setUp(self):

        self.client = SoapClient(
            wsdl = WSDL,        
            cache = None,
            ns="tzmed",
            soap_ns="soapenv",
            soap_server="jetty",                # needed to handle list
            trace = "--trace" in sys.argv)
            
        # fix location (localhost:9050 is erroneous in the WSDL)
        self.client.services['IWebServiceService']['ports']['IWebServicePort']['location'] = LOCATION
            
        # Set WSSE security credentials
        self.client['wsse:Security'] = {
            'wsse:UsernameToken': {
                'wsse:Username': 'testwservice',
                'wsse:Password': 'testwservicepsw',
                }
            }

    def test_send_medicamentos(self):
        #self.client.help("sendMedicamentos")
        
        # Create the complex type (medicament data transfer object):
        medicamentosDTO = dict(
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now() + 
                         datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            numero_serial=int(time.time()), 
            id_obra_social=None, id_evento=134,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_docmento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="1688", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555",
            )
        
        # Call the webservice to inform a medicament:
        res = self.client.sendMedicamentos(
            arg0=medicamentosDTO,
            arg1='pruebasws', 
            arg2='pruebasws',
        )

        # Analyze the response:
        ret = res['return']        
        self.assertIsInstance(ret['codigoTransaccion'], unicode)
        self.assertEqual(ret['resultado'], True)

    def test_send_medicamentos_dh_serie(self):
        self.client.help("sendMedicamentosDHSerie")
        
        # Create the complex type (medicament data transfer object):
        medicamentosDTODHSerie = dict(
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now() + 
                         datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            desde_numero_serial=10,
            hasta_numero_serial=0, 
            id_obra_social=None, id_evento=134,
            )
        
        # Call the webservice to inform a medicament:
        res = self.client.sendMedicamentosDHSerie(
            arg0=medicamentosDTODHSerie, 
            arg1='pruebasws', 
            arg2='pruebasws',
        )

        # Analyze the response:
        ret = res['return']
        
        # Check the results:
        self.assertIsInstance(ret['codigoTransaccion'], unicode)
        self.assertEqual(ret['errores'][0]['_c_error'], '3004')
        self.assertEqual(ret['errores'][0]['_d_error'], "El campo Hasta Nro Serial debe ser mayor o igual al campo Desde Nro Serial.")
        self.assertEqual(ret['resultado'], False)

    def test_get_transacciones_no_confirmadas(self):

        # Call the webservice to query all the un-confirmed transactions:
        res = self.client.getTransaccionesNoConfirmadas(
                arg0='pruebasws', 
                arg1='pruebasws',
            )
        
        # Analyze the response:
        ret = res['return']

        # Check the results (a list should be returned):
        self.assertIsInstance(ret['list'], list)
        
        for transaccion_plain_ws in ret['list']:
            # each item of the list is a dict (transaccionPlainWS complex type):
            # {'_f_evento': u'20/06/2012', '_numero_serial': u'04', ...}
            # check the keys returned in the complex type:
            for key in ['_f_evento', '_f_transaccion', '_lote', 
                        '_numero_serial', '_razon_social_destino', 
                        '_gln_destino', '_n_remito', '_vencimiento', 
                        '_d_evento', '_id_transaccion_global', 
                        '_razon_social_origen', '_n_factura', '_gln_origen', 
                        '_id_transaccion', '_gtin', '_nombre']:
                self.assertIn(key, transaccion_plain_ws)


if __name__ == '__main__':
    unittest.main()
        
