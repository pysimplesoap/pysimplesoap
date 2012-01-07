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

import os
import unittest
import sys
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
            #soap_server="jbossas6",
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
        self.client.help("sendMedicamentos")
        res = self.client.sendMedicamentos(
            arg0={  'f_evento': "25/11/2011", 
                    'h_evento': "04:24", 
                    'gln_origen': "glnws" , 
                    'gln_destino': "glnws", 
                    'n_remito': "1234", 
                    'n_factura': "1234", 
                    'vencimiento': "30/11/2011", 
                    'gtin': "GTIN1", 
                    'lote': "1111", 
                    'numero_serial': "12345", 
                    'id_obra_social': 1, 
                    'id_evento': 133, 
                    'cuit_origen': "20267565393", 
                    'cuit_destino': "20267565393", 
                    'apellido': "Reingart", 
                    'nombres': "Mariano", 
                    'tipo_docmento': "96", 
                    'n_documento': "26756539", 
                    'sexo': "M", 
                    'direccion': "Saraza", 
                    'numero': "1234", 
                    'piso': "", 
                    'depto': "", 
                    'localidad': "Hurlingham", 
                    'provincia': "Buenos Aires", 
                    'n_postal': "B1688FDD",
                    'fecha_nacimiento': "01/01/2000", 
                    'telefono': "5555-5555",
                    }, 
            arg1='pruebasws', 
            arg2='pruebasws',
        )

        ret = res['return']
        
        self.assertEqual(ret[0]['codigoTransaccion'], None)
        self.assertEqual(ret[1]['errores']['_c_error'], '3019')
        self.assertEqual(ret[1]['errores']['_d_error'], "No ha informado la recepcion del medicamento que desea enviar.")
        self.assertEqual(ret[-1]['resultado'], False)


    def test_send_medicamentos_dh_serie(self):
        self.client.help("sendMedicamentosDHSerie")
        res = self.client.sendMedicamentosDHSerie(
            arg0={  'f_evento': "25/11/2011", 
                    'h_evento': "04:24", 
                    'gln_origen': "glnws" , 
                    'gln_destino': "glnws", 
                    'n_remito': "1234", 
                    'n_factura': "1234", 
                    'vencimiento': "30/11/2011", 
                    'gtin': "GTIN1", 
                    'lote': "1111", 
                    'desde_numero_serial': 2, 
                    'hasta_numero_serial': 1, 
                    'id_obra_social': 1, 
                    'id_evento': 133, 
                    'cuit_origen': "20267565393", 
                    'cuit_destino': "20267565393", 
                    'apellido': "Reingart", 
                    'nombres': "Mariano", 
                    'tipo_docmento': "96", 
                    'n_documento': "26756539", 
                    'sexo': "M", 
                    'direccion': "Saraza", 
                    'numero': "1234", 
                    'piso': "", 
                    'depto': "", 
                    'localidad': "Hurlingham", 
                    'provincia': "Buenos Aires", 
                    'n_postal': "B1688FDD",
                    'fecha_nacimiento': "01/01/2000", 
                    'telefono': "5555-5555",
                    }, 
            arg1='pruebasws', 
            arg2='pruebasws',
        )

        ret = res['return']
        
        self.assertEqual(ret[0]['codigoTransaccion'], None)
        self.assertEqual(ret[1]['errores']['_c_error'], '3004')
        self.assertEqual(ret[1]['errores']['_d_error'], "El campo Hasta Nro Serial debe ser mayor o igual al campo Desde Nro Serial.")
        self.assertEqual(ret[-1]['resultado'], False)


