import os
from .base import BaseTestcase
from pysimplesoap.api import decode


wsdl=os.path.abspath('utest/data/ne3s.wsdl')


class TestMsgDecoding(BaseTestcase):
    def test_decode_mime_with_xml_only_msg(self):
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

    def test_decode_multiple_mimes_msg(self):
        headers = {'content-type': 'multipart/related; boundary=MIMEBoundaryurn_uuid_41C3C1F5C427229F7A1466676077706; type="text/xml"; start="<0.urn:uuid:41C3C1F5C427229F7A1466676077707@apache.org>"', 'soapaction': '"http://www.nokiasiemens.com/ne3s/1.0/transferNotification"','transfer-encoding':'chunked'}
        resp = decode(headers, self.get_data('multi_mime'), wsdl=wsdl)
        self.assertEqual(resp['queueId'], 'ne3s_atl_logUploadNotificationQueue')
        self.assertEqual(resp['sequenceNumber'], 11),
        self.assertEqual(resp['attachmentProperties']['contentType'], 'oats')
        self.assertIn('transferNotificationContent1466676077553@nokiasiemens.com', resp)
        self.assertNotIn('', resp)
        attachment = resp['transferNotificationContent1466676077553@nokiasiemens.com']
        self.assertEqual(attachment['log']['@logFileName'], 'AUDIT_LOG')
        self.assertEqual(attachment['log']['@logType'], 'AUDIT_LOG')
        self.assertEqual(attachment['log']['record']['interfaceType'], 'ne3s_ws')

