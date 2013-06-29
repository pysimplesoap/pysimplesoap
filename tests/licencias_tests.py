#!/usr/bin/python
# -*- coding: latin1 -*-

import unittest
from pysimplesoap.client import SoapClient, SoapFault
from dummy_utils import DummyHTTP, TEST_DIR
import os

xml = open(os.path.join(TEST_DIR, "licencias.xml")).read()

class TestIssues(unittest.TestCase):

    def test_buscar_personas_raw(self):

        url = "http://www.testgobi.dpi.sfnet/licencias/web/soap.php"
        client = SoapClient(location=url, ns="web", trace=True,
                            namespace="http://wwwdesagobi.dpi.sfnet:8080/licencias/web/",
                            action=url)
        # load dummy response (for testing)
        client.http = DummyHTTP(xml)
        client['AuthHeaderElement'] = {'username': 'mariano', 'password': 'clave'}
        response = client.PersonaSearch(persona=(('numero_documento', '99999999'),
                                                  ('apellido_paterno', ''),
                                                  ('apellido_materno', ''),
                                                  ('nombres', ''),
                                                  ))

        # the raw response is a SimpleXmlElement object:
        
        self.assertEqual(str(response.result.item[0]("xsd:string")[0]), "resultado")
        self.assertEqual(str(response.result.item[0]("xsd:string")[1]), "true")
        self.assertEqual(str(response.result.item[1]("xsd:string")[0]), "codigo")
        self.assertEqual(str(response.result.item[1]("xsd:string")[1]), "WS01-01")
        self.assertEqual(str(response.result.item[2]("xsd:string")[0]), "mensaje")
        self.assertEqual(str(response.result.item[2]("xsd:string")[1]), "Se encontraron 1 personas.")
        self.assertEqual(str(response.result.item[2]("xsd:string")[0]), "mensaje")
        self.assertEqual(str(response.result.item[2]("xsd:string")[1]), "Se encontraron 1 personas.")

        self.assertEqual(str(response.result.item[3]("xsd:anyType")[0]), "datos")
        self.assertEqual(str(response.result.item[3]("xsd:anyType")[1]("ns2:Map").item[0].key), "lic_ps_ext_id")
        self.assertEqual(str(response.result.item[3]("xsd:anyType")[1]("ns2:Map").item[0].value), "123456")
        self.assertEqual(str(response.result.item[3]("xsd:anyType")[1]("ns2:Map").item[10].key), "fecha_nacimiento")
        self.assertEqual(str(response.result.item[3]("xsd:anyType")[1]("ns2:Map").item[10].value), "1985-10-02 00:00:00")
    

    def test_buscar_personas_wsdl(self):
        WSDL = "file://" + os.path.join(TEST_DIR, "licencias.wsdl")
        client = SoapClient(wsdl=WSDL, ns="web", trace=True)
        print client.help("PersonaSearch")
        client['AuthHeaderElement'] = {'username': 'mariano', 'password': 'clave'}
        client.http = DummyHTTP(xml)
        resultado = client.PersonaSearch(numero_documento='31867063')
        print resultado
        
        # each resultado['result'][i]['item'] is xsd:anyType, so it is not unmarshalled 
        # they are SimpleXmlElement (see test_buscar_personas_raw)
        self.assertEqual(str(resultado['result'][0]['item']('xsd:string')[0]), "resultado")
        self.assertEqual(str(resultado['result'][1]['item']('xsd:string')[1]), "WS01-01")
        self.assertEqual(str(resultado['result'][3]['item']('xsd:anyType')[1]("ns2:Map").item[10].value), "1985-10-02 00:00:00")

    

