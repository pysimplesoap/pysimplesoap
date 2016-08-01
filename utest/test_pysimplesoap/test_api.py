import os
from .base import BaseTestcase
from pysimplesoap.api import decode


wsdl=os.path.abspath('utest/data/register.wsdl')


class TestMsgDecoding(BaseTestcase):
    def test_decode_startRegistration_msg(self):
        headers = {
            'soapaction': 'http://www.nokiasiemens.com/ne3s/1.0/startRegistration',
            'content-type': 'multipart/related; boundary="MIMEBoundary_37b1639e1b936afbe7bfb91e329eda80160d10652a34d791"; type="text/xml"; start="<0.27b1639e1b936afbe7bfb91e329eda80160d10652a34d791@apache.org>"',
            'server': 'Jetty(9.2.z-SNAPSHOT)'
            }
        resp = decode(headers, self.get_data('mime_with_xml_only'), wsdl=wsdl)
        self.assertEqual(resp['agentIdentity']['release'], '4.5')
        self.assertEqual(resp['agentIdentity']['type'], 'BTS')
        self.assertEqual(resp['agentIdentity']['uniqueId'], 'PLMN-PLMN/SBTS-1735')
        self.assertEqual(resp['agentIdentity']['vendor'], 'NSN')
        self.assertEqual(resp['agentNonce'], 'VUV4TlRpMVFURTFPTDFOQ1ZGTXRNVGN6TlE9PQ==')
        self.assertEqual(resp['agentResponse'], 'AQI=')
        self.assertEqual(resp['licenseRequired'], False)
        self.assertEqual(resp['registrationComplete'], True)

