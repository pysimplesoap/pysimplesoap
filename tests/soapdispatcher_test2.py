# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pysimplesoap.server import SoapDispatcher
import unittest


def dummy(in0):
    "Just return input"
    return in0


class TestSoapDispatcher(unittest.TestCase):
    def setUp(self):
        self.disp = SoapDispatcher(
            name="PySimpleSoapSample",
            location="http://localhost:8008/",
            action='http://localhost:8008/',  # SOAPAction
            namespace="http://example.com/pysimplesoapsamle/", prefix="ns0",
            documentation='Example soap service using PySimpleSoap',
            debug=True,
            ns=True)

        self.disp.register_function('dummy', dummy,
                                    returns={'out0': str},
                                    args={'in0': str}
                                    )
        self.disp.register_function('dummy_response_element', dummy,
                                    returns={'out0': str},
                                    args={'in0': str},
                                    response_element_name='diffRespElemName'
                                    )

    def test_zero(self):
        response = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><dummyResponse xmlns="http://example.com/pysimplesoapsamle/"><out0>Hello world</out0></dummyResponse></soap:Body></soap:Envelope>"""

        request = """\
<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema">
       <soap:Body>
         <dummy xmlns="http://example.com/sample.wsdl">
           <in0 xsi:type="xsd:string">Hello world</in0>
        </dummy>
       </soap:Body>
    </soap:Envelope>"""
        self.assertEqual(self.disp.dispatch(request), response)

    def test_response_element_name(self):
        response = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><diffRespElemName xmlns="http://example.com/pysimplesoapsamle/"><out0>Hello world</out0></diffRespElemName></soap:Body></soap:Envelope>"""

        request = """\
<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema">
       <soap:Body>
         <dummy_response_element xmlns="http://example.com/sample.wsdl">
           <in0 xsi:type="xsd:string">Hello world</in0>
        </dummy_response_element>
       </soap:Body>
    </soap:Envelope>"""
        self.assertEqual(self.disp.dispatch(request), response)

    # def test_wsdl(self):
    #     response = """<?xml version="1.0" encoding="UTF-8"?>"""
    #     self.assertEqual(self.disp.wsdl(), response)


if __name__ == '__main__':
    unittest.main()
