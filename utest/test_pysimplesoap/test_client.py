import os
from .base import BaseTestcase
from pysimplesoap.simplexml import SimpleXMLElement
from pysimplesoap.client import SoapClient


client = SoapClient(wsdl=os.path.abspath('utest/data/register.wsdl'))
ns = 'http://schemas.xmlsoap.org/soap/envelope/'


class TestSimpleXmlElement(BaseTestcase):
    def test_get_normal_xml(self):
        pass

    def test_get_MIME_with_xml_only(self):
        # {'status': 200,
            # 'content-type': 'multipart/related; boundary="MIMEBoundary_bbea0d2aa0d4b9c1867f0328ee1c77dc9a2a8dae8581dea4"; type="text/xml"; start="<"0.abea0d2aa0d4b9c1867f0328ee1c77dc9a2a8dae8581dea4@apache.org>""',
            # 'server': 'Jetty(9.2.z-SNAPSHOT)'
            # }
        response = SimpleXMLElement(self.get_data('mime_with_xml_only'))
        output = client.get_operation('startRegistration')['output']
        resp = response('Body', ns=ns).children().unmarshall(output, strict=True)
        self.assertEqual(resp['startRegistrationResponse']['agentIdentity']['type'], 'BTS')

    def test_get_MIME_with_multi_boundaries(self):
        pass
