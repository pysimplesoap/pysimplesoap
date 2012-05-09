# coding: utf-8

import datetime
import unittest
from pysimplesoap.server import SoapDispatcher
from pysimplesoap.simplexml import Date, Decimal

def adder(p, c, dt=None):
    "Add several values"
    dt = dt + datetime.timedelta(365)
    return {'ab': p['a']+p['b'], 'dd': c[0]['d']+c[1]['d'], 'dt': dt}

def dummy(in0):
    "Just return input"
    return in0

def echo(request):
    "Copy request->response (generic, any type)"
    return request.value


class TestSoapDispatcher(unittest.TestCase):
    def eq(self, value, expectation, msg=None):
        if msg is not None:
            msg += ' %s' % value
            self.assertEqual(value, expectation, msg)
        else:
            self.assertEqual(value, expectation, "%s\n---\n%s" % (value, expectation))
    
    def setUp(self):
        self.dispatcher = SoapDispatcher(
            name = "PySimpleSoapSample",
            location = "http://localhost:8008/",
            action = 'http://localhost:8008/', # SOAPAction
            namespace = "http://example.com/pysimplesoapsamle/", prefix="ns0",
            documentation = 'Example soap service using PySimpleSoap',
            trace = True,
            ns = True)
        
        self.dispatcher.register_function('Adder', adder,
            returns={'AddResult': {'ab': int, 'dd': str } },
            args={'p': {'a': int,'b': int}, 'dt': Date, 'c': [{'d': Decimal}]})
        
        self.dispatcher.register_function('Dummy', dummy,
            returns={'out0': str},
            args={'in0': str})
        
        self.dispatcher.register_function('Echo', echo)
        
    def test_classic_dialect(self):
        # adder local test (clasic soap dialect)
        resp = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><AdderResponse xmlns="http://example.com/pysimplesoapsamle/"><dd>5000000.3</dd><ab>3</ab><dt>2011-07-24</dt></AdderResponse></soap:Body></soap:Envelope>"""
        xml = """<?xml version="1.0" encoding="UTF-8"?> 
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
       <soap:Body>
         <Adder xmlns="http://example.com/sample.wsdl">
           <p><a>1</a><b>2</b></p><c><d>5000000.1</d><d>.2</d></c><dt>2010-07-24</dt>
        </Adder>
       </soap:Body>
    </soap:Envelope>"""
        self.eq(self.dispatcher.dispatch(xml), resp)
        
    def test_modern_dialect(self):
        # adder local test (modern soap dialect, SoapUI)
        resp = """<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:pys="http://example.com/pysimplesoapsamle/" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><pys:AdderResponse><dd>15.021</dd><ab>12</ab><dt>1970-07-20</dt></pys:AdderResponse></soapenv:Body></soapenv:Envelope>"""
        xml = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:pys="http://example.com/pysimplesoapsamle/">
   <soapenv:Header/>
   <soapenv:Body>
      <pys:Adder>
         <pys:p><pys:a>9</pys:a><pys:b>3</pys:b></pys:p>
         <pys:dt>1969-07-20<!--1969-07-20T21:28:00--></pys:dt>
         <pys:c><pys:d>10.001</pys:d><pys:d>5.02</pys:d></pys:c>
      </pys:Adder>
   </soapenv:Body>
</soapenv:Envelope>
    """
        self.eq(self.dispatcher.dispatch(xml), resp)
        
    def test_echo(self):
        # echo local test (generic soap service)
        resp = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><EchoResponse xmlns="http://example.com/pysimplesoapsamle/"><value xsi:type="xsd:string">Hello world</value></EchoResponse></soap:Body></soap:Envelope>"""
        xml = """<?xml version="1.0" encoding="UTF-8"?> 
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema">
       <soap:Body>
         <Echo xmlns="http://example.com/sample.wsdl">
           <value xsi:type="xsd:string">Hello world</value>
        </Echo>
       </soap:Body>
    </soap:Envelope>"""
        self.eq(self.dispatcher.dispatch(xml), resp)
    
if __name__ == '__main__':
    unittest.main()

