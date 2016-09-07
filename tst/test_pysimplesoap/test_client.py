import os
import re
from .base import BaseTestcase
from pysimplesoap.simplexml import SimpleXMLElement
from pysimplesoap.client import SoapClient


client = SoapClient(wsdl=os.path.abspath('tst/data/ne3s.wsdl'))
ns = 'http://schemas.xmlsoap.org/soap/envelope/'
kwargs = {u'soc': u'cid:12345', u'reRegisterInterval': u'20', u'managerIdentity': {u'release': u'1.0'}, u'agentUniqueId': u'lyj0034', u'notificationConsumerURL': u'http://localhost:30505/services', u'managerNonce': u'ODYzNTQ0NTg0'}

class TestSimpleXmlElement(BaseTestcase):
    def test_method_element_list(self):
        self.assertEqual( client.get_operation('startRegistration')['input']['startRegistration'].keys(), [u'managerIdentity', u'agentUniqueId', u'notificationConsumerURL', u'reRegisterInterval', u'managerNonce', u'extensions', u'soc'])
        self.assertEqual( client.get_operation('transferNotification')['input']['transferNotification'].keys(), [u'agentRegistrationId', u'agentRegistrationKey', u'queueId', u'notificationType', u'sequenceNumber', u'attachmentProperties', u'extensions', u'notificationContent'])

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


class TestGenerateClientRequest(BaseTestcase):
    def test_generate_normal_xml_request(self):
        self.assertEqual(client._generate_request('startRegistration', (), {}, []), ({}, '''<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<soap:Header/>
<soap:Body>
    <startRegistration xmlns="">
    </startRegistration>
</soap:Body>
</soap:Envelope>'''))

    def test_generate_mime_request(self):
        header, body = client._generate_request('startRegistration', (), kwargs, [('abcde', '12345')])
        self.assertIn('multipart/related', header['Content-type'])
        ptn = re.compile(r'--\S+')
        self.assertEqual(ptn.sub('', body).replace('\r\n', '\n'), ptn.sub('', '''--8cf32b7e-5a0c-11e6-9fa3-080027d14c2a
Content-Type: text/xml

<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<soap:Header/>
<soap:Body>
    <startRegistration xmlns="">
    <managerIdentity><release>1.0</release></managerIdentity><agentUniqueId>lyj0034</agentUniqueId><notificationConsumerURL>http://localhost:30505/services</notificationConsumerURL><reRegisterInterval>20</reRegisterInterval><managerNonce>ODYzNTQ0NTg0</managerNonce><soc>cid:12345</soc></startRegistration>
</soap:Body>
</soap:Envelope>
--8cf32b7e-5a0c-11e6-9fa3-080027d14c2a
Content-Id:<abcde>
Content-Type: application/octet-stream
Content-Transfer-Encoding: bindary

12345
--8cf32b7e-5a0c-11e6-9fa3-080027d14c2a--'''))

