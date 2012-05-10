# coding: utf-8

import logging
import unittest
from pysimplesoap.server import SoapDispatcher

log = logging.getLogger('pysimplesoap.server')
log.setLevel(logging.DEBUG)

REQ = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ext="http://external.mt.moboperator" xmlns:mod="http://model.common.mt.moboperator">
   <soapenv:Header/>
   <soapenv:Body>
      <ext:activateSubscriptions>
         <ext:serviceMsisdn>791</ext:serviceMsisdn>
         <ext:serviceName>abc</ext:serviceName>
         <ext:activations>
            <!--1 or more repetitions:-->
            <mod:items>
               <mod:msisdn>791000000</mod:msisdn>
               <!--1 or more repetitions:-->
               <mod:properties>
                  <mod:name>x</mod:name>
                  <mod:value>2</mod:value>
               </mod:properties>
               <mod:parameters> ::260013456789</mod:parameters>
            </mod:items>
         </ext:activations>
      </ext:activateSubscriptions>
   </soapenv:Body>
</soapenv:Envelope>"""

SINGLE_NS_RESP = """<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:ext="http://external.mt.moboperator" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><ext:activateSubscriptionsResponse><activateSubscriptionsReturn><code>0</code><description>desc</description><items><msisdn>791000000</msisdn><properties><name>x</name><value>2</value></properties><status>0</status></items></activateSubscriptionsReturn></ext:activateSubscriptionsResponse></soapenv:Body></soapenv:Envelope>"""

class TestServerMultiNS(unittest.TestCase):

    def _single_ns_func(self, serviceMsisdn, serviceName, activations=[]):
        code = 0
        desc = 'desc'

        results = [{
            'items': [
                {'msisdn': '791000000'},
                {'properties': [{'name': 'x'}, {'value': '2'}]},
                {'status': '0'}
            ]}]

        ret = {
            'activateSubscriptionsReturn': [
                {'code': code},
                {'description': desc},
            ]}
        ret['activateSubscriptionsReturn'].extend(results)
        return ret
    
    _single_ns_func.returns = {'non-empty-dict': 1}
    _single_ns_func.args = {
        'serviceMsisdn': str,
        'serviceName': str,
        'activations': [
            {'items': {
                    'msisdn': str,
                    'status': int,
                    'parameters': str,
                    'properties': ({
                            'name': str,
                            'value': str
                        },
                    )
                }
            }
        ]
    }
    
    def test_single_ns(self):
        dispatcher = SoapDispatcher(
            name = "MTClientWS",
            location = "http://localhost:8008/ws/MTClientWS",
            action = 'http://localhost:8008/ws/MTClientWS', # SOAPAction
            namespace = "http://external.mt.moboperator", prefix="external",
            documentation = 'moboperator MTClientWS',
            ns = True,
            pretty=False,
            debug=True)
        
        dispatcher.register_function('activateSubscriptions', 
            self._single_ns_func,
            returns=self._single_ns_func.returns,
            args=self._single_ns_func.args)
        
        
        self.assertEqual(dispatcher.dispatch(REQ), SINGLE_NS_RESP)
        
    # def test_multi_ns(self):
    #     pass
    
    
if __name__ == '__main__':
    unittest.main()
