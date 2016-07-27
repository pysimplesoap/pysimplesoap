import os
from .base import BaseTestcase
from pysimplesoap.simplexml import SimpleXMLElement
from pysimplesoap.client import SoapClient


client = SoapClient(wsdl=os.path.abspath('utest/data/register.wsdl'))
ns = 'http://schemas.xmlsoap.org/soap/envelope/'


class TestSimpleXmlElement(BaseTestcase):
    def test_get_normal_xml(self):
        response = SimpleXMLElement(self.get_data('normal_xml'))
        output = client.get_operation('startRegistration')['output']
        resp = response('Body', ns=ns).children().unmarshall(output, strict=True)
        self.assertEqual(resp['startRegistrationResponse']['agentIdentity']['type'], 'BTS')

    def test_get_MIME_with_xml_only(self):
        headers = {'status': 200,
            'content-type': 'multipart/related; boundary="MIMEBoundary_37b1639e1b936afbe7bfb91e329eda80160d10652a34d791"; type="text/xml"; start="<0.27b1639e1b936afbe7bfb91e329eda80160d10652a34d791@apache.org>"',
            'server': 'Jetty(9.2.z-SNAPSHOT)'
            }
        response = SimpleXMLElement(self.get_data('mime_with_xml_only'), headers=headers)
        output = client.get_operation('startRegistration')['output']
        resp = response('Body', ns=ns).children().unmarshall(output, strict=True)
        self.assertEqual(resp['startRegistrationResponse']['agentIdentity']['type'], 'BTS')

    def test_get_MIME_with_multi_boundaries(self):
        # TODO
        pass
