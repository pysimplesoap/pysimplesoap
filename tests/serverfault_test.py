# -*- coding: utf-8 -*-

import unittest
from pysimplesoap.server import SoapDispatcher, SoapFault
from pysimplesoap.simplexml import SimpleXMLElement


class ServerSoapFaultTest(unittest.TestCase):
    def setUp(self):
        self.dispatcher = SoapDispatcher(
            'Test',
            action='http://localhost:8008/soap',
            location='http://localhost:8008/soap'
        )

        def divider(a, b):
            if b == 0:
                raise SoapFault(faultcode='DivisionByZero', faultstring='Division by zero not allowed', detail='test')
            return float(a) / b

        self.dispatcher.register_function(
            'Divider', divider,
            returns={'DivideResult': float},
            args={'a': int, 'b': int}
        )

    def test_exception(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
           <soap:Body>
             <Divider xmlns="http://example.com/sample.wsdl">
               <a>100</a><b>2</b>
            </Divider>
           </soap:Body>
        </soap:Envelope>"""
        response = SimpleXMLElement(self.dispatcher.dispatch(xml))
        self.assertEqual(str(response.DivideResult), '50.0')

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
           <soap:Body>
             <Divider xmlns="http://example.com/sample.wsdl">
               <a>100</a><b>0</b>
            </Divider>
           </soap:Body>
        </soap:Envelope>"""
        response = SimpleXMLElement(self.dispatcher.dispatch(xml))
        body = getattr(getattr(response, 'soap:Body'), 'soap:Fault')
        self.assertIsNotNone(body)
        self.assertEqual(str(body.faultcode), 'Server.DivisionByZero')
        self.assertEqual(str(body.faultstring), 'Division by zero not allowed')
        self.assertEqual(str(body.detail), 'test')
