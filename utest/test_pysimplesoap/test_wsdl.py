import os
from .base import BaseTestcase
from pysimplesoap.wsdl import parse


class TestWsdlParsing(BaseTestcase):
    def test_with_import(self):
        services = parse(os.path.abspath('utest/data/register.wsdl'))
        self.assertEqual(services.keys(), ['NE3SRegistrationService'])
        self.assertEqual(services['NE3SRegistrationService']['documentation'], '')
        self.assertEqual(services['NE3SRegistrationService']['ports']['ne3sRegistration']['operations']['startRegistration']['output']['startRegistrationResponse']['agentIdentity']['uniqueId'], str)

