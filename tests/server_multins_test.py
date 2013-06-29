# coding: utf-8

import logging
import unittest
from pysimplesoap.server import SoapDispatcher

# log = logging.getLogger('pysimplesoap.server')
# log.setLevel(logging.DEBUG)
# log = logging.getLogger('pysimplesoap.simplexml')
# log.setLevel(logging.DEBUG)

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

REQ1 = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Header/><soapenv:Body><p727:updateDeliveryStatus xmlns:p727="http://external.mt.moboperator"><p727:serviceMsisdn>51072</p727:serviceMsisdn><p727:serviceName>IPLA</p727:serviceName><p727:messageDeliveryStatuses><p924:items xmlns:p924="http://model.common.mt.moboperator"><p924:msisdn>48726401494</p924:msisdn><p924:status>380</p924:status><p924:deliveryId>33946812</p924:deliveryId></p924:items></p727:messageDeliveryStatuses></p727:updateDeliveryStatus></soapenv:Body></soapenv:Envelope>"""

SINGLE_NS_RESP = """<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:ext="http://external.mt.moboperator" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><ext:activateSubscriptionsResponse><activateSubscriptionsReturn><code>0</code><description>desc</description><items><msisdn>791000000</msisdn><properties><name>x</name><value>2</value></properties><status>0</status></items></activateSubscriptionsReturn></ext:activateSubscriptionsResponse></soapenv:Body></soapenv:Envelope>"""

MULTI_NS_RESP = """<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:ext="http://external.mt.moboperator" xmlns:mod="http://model.common.mt.moboperator" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><ext:activateSubscriptionsResponse><ext:activateSubscriptionsReturn><mod:code>0</mod:code><mod:description>desc</mod:description><mod:items><mod:msisdn>791000000</mod:msisdn><mod:properties><mod:name>x</mod:name><mod:value>2</mod:value></mod:properties><mod:status>0</mod:status></mod:items></ext:activateSubscriptionsReturn></ext:activateSubscriptionsResponse></soapenv:Body></soapenv:Envelope>"""
MULTI_NS_RESP1 = """<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:p727="http://external.mt.moboperator" xmlns:p924="http://model.common.mt.moboperator" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><p727:updateDeliveryStatusResponse><p727:updateDeliveryStatusReturn><p924:code>0</p924:code><p924:description>desc</p924:description></p727:updateDeliveryStatusReturn></p727:updateDeliveryStatusResponse></soapenv:Body></soapenv:Envelope>"""

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

    def _updateDeliveryStatus(self, serviceMsisdn, serviceName, messageDeliveryStatuses=[]):
        code = 0
        desc = 'desc'
        return {
            'external:updateDeliveryStatusReturn': [
                {'model:code': code},
                {'model:description': desc}
            ]
        }
    _updateDeliveryStatus.returns = {'non-empty-dict': 1}
    _updateDeliveryStatus.args = {
        'serviceMsisdn': str,
        'serviceName': str,
        'messageDeliveryStatuses': [
            {'items': {
                    'msisdn': str,
                    'status': int,
                    'deliveryId': str,
                    'properties': ({
                            'name': str,
                            'value': int
                        },
                    )
                }
            }
        ]
    }
        
    def _multi_ns_func(self, serviceMsisdn, serviceName, activations=[]):
        code = 0
        desc = 'desc'

        results = [{
            'model:items': [
                {'model:msisdn': '791000000'},
                {'model:properties': [{'model:name': 'x'}, {'model:value': '2'}]},
                {'model:status': '0'}
            ]}]

        ret = {
            'external:activateSubscriptionsReturn': [
                {'model:code': code},
                {'model:description': desc},
            ]}
        ret['external:activateSubscriptionsReturn'].extend(results)
        return ret
    
    _multi_ns_func.returns = {'non-empty-dict': 1}
    _multi_ns_func.args = {
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
        
        # I don't fully know if that is a valid response for a given request,
        # but I tested it, to be sure that a multi namespace function
        # doesn't brake anything.
        self.assertEqual(dispatcher.dispatch(REQ), SINGLE_NS_RESP)
        
    def test_multi_ns(self):
        dispatcher = SoapDispatcher(
            name = "MTClientWS",
            location = "http://localhost:8008/ws/MTClientWS",
            action = 'http://localhost:8008/ws/MTClientWS', # SOAPAction
            namespace = "http://external.mt.moboperator", prefix="external",
            documentation = 'moboperator MTClientWS',
            namespaces = {
                'external': 'http://external.mt.moboperator', 
                'model': 'http://model.common.mt.moboperator'
            },
            ns = True,
            pretty=False,
            debug=True)
        
        dispatcher.register_function('activateSubscriptions', 
            self._multi_ns_func,
            returns=self._multi_ns_func.returns,
            args=self._multi_ns_func.args)
        dispatcher.register_function('updateDeliveryStatus',
            self._updateDeliveryStatus,
            returns=self._updateDeliveryStatus.returns,
            args=self._updateDeliveryStatus.args)
        
        self.assertEqual(dispatcher.dispatch(REQ), MULTI_NS_RESP)
        self.assertEqual(dispatcher.dispatch(REQ1), MULTI_NS_RESP1)
    
if __name__ == '__main__':
    unittest.main()
