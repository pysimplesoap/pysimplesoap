# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
from pysimplesoap.client import SoapClient, SimpleXMLElement, SoapFault

import sys
if sys.version > '3':
    basestring = str


class TestIssues(unittest.TestCase):

    def test_issue19(self):
        """Test xsd namespace found under schema elementes"""
        client = SoapClient(
            wsdl='http://uat.destin8.co.uk:80/ChiefEDI/ChiefEDI?wsdl'
        )

    def test_issue34(self):
        """Test soap_server SoapClient constructor parameter"""
        client = SoapClient(
            wsdl="http://eklima.met.no/metdata/MetDataService?WSDL",
            soap_server="oracle", cache=None
        )
        ##print(client.help("getStationsProperties"))
        ##print(client.help("getValidLanguages"))

        # fix bad wsdl: server returns "getValidLanguagesResponse"
        # instead of "getValidLanguages12Response"
        met_data = client.services['MetDataService']['ports']['MetDataServicePort']
        languages = met_data['operations']['getValidLanguages']
        output = languages['output']['getValidLanguages12Response']
        languages['output'] = {'getValidLanguagesResponse': output}

        lang = client.getValidLanguages()

        self.assertEqual(lang, {'return': ['no', 'en', 'ny']})

    def test_issue35_raw(self):

        client = SoapClient(
            location="http://wennekers.epcc.ed.ac.uk:8080"
                     "/axis/services/MetadataCatalogue",
            action=""
        )
        response = client.call(
            "doEnsembleURIQuery",
            ("queryFormat", "Xpath"),
            ("queryString", "/markovChain"),
            ("startIndex", 0),
            ("maxResults", -1)
        )
        self.assertEqual(str(response.statusCode), "MDC_INVALID_REQUEST")
        #print(str(response.queryTime))
        self.assertEqual(int(response.totalResults), 0)
        self.assertEqual(int(response.startIndex), 0)
        self.assertEqual(int(response.numberOfResults), 0)

        for result in response.results:
            print(str(result))

    def test_issue35_wsdl(self):
        """Test positional parameters, multiRefs and axis messages"""

        client = SoapClient(
            wsdl="http://wennekers.epcc.ed.ac.uk:8080/axis/services/MetadataCatalogue?WSDL",
            soap_server="axis"
        )
        response = client.doEnsembleURIQuery(
            queryFormat="Xpath", queryString="/markovChain",
            startIndex=0, maxResults=-1
        )

        ret = response['doEnsembleURIQueryReturn']
        self.assertEqual(ret['statusCode'], "MDC_INVALID_REQUEST")
        self.assertEqual(ret['totalResults'], 0)
        self.assertEqual(ret['startIndex'], 0)
        self.assertEqual(ret['numberOfResults'], 0)

    def test_issue8_raw(self):
        """Test europa.eu tax service (namespace - raw call)"""

        client = SoapClient(
            location="http://ec.europa.eu/taxation_customs/vies/services/checkVatService",
            action='',  # SOAPAction
            namespace="urn:ec.europa.eu:taxud:vies:services:checkVat:types"
        )
        vat = 'IE6388047V'
        code = vat[:2]
        number = vat[2:]
        res = client.checkVat(countryCode=code, vatNumber=number)
        self.assertEqual(str(res('countryCode')), "IE")
        self.assertEqual(str(res('vatNumber')), "6388047V")
        self.assertEqual(str(res('name')), "GOOGLE IRELAND LIMITED")
        self.assertEqual(str(res('address')), "1ST & 2ND FLOOR ,GORDON HOUSE ,"
                                              "BARROW STREET ,DUBLIN 4")

    def test_issue8_wsdl(self):
        """Test europa.eu tax service (namespace - wsdl call)"""
        URL='http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl'
        client = SoapClient(wsdl=URL)
        # check the correct target namespace:
        self.assertEqual(client.namespace,
                         "urn:ec.europa.eu:taxud:vies:services:checkVat:types")
        # call the webservice to check everything else:
        vat = 'BE0897290877'
        code = vat[:2]
        number = vat[2:]
        res = client.checkVat(countryCode=code, vatNumber=number)
        # check returned values:
        self.assertEqual(res['name'], "SPRL B2CK")
        self.assertEqual(res['address'], "RUE DE ROTTERDAM 4 B21\n"
                                         "4000  LIEGE")

    ## NOTE: Missing file "ups.wsdl"
    ##def test_ups(self):
    ##    "Test UPS tracking service"
    ##    WSDL = "file:ups.wsdl"
    ##    client = SoapClient(wsdl=WSDL, ns="web")
    ##    print(client.help("ProcessTrack"))

    def test_issue43(self):

        client = SoapClient(
            wsdl="https://api.clarizen.com/v1.0/Clarizen.svc"
        )

        print(client.help("Login"))
        print(client.help("Logout"))
        print(client.help("Query"))
        print(client.help("Metadata"))
        print(client.help("Execute"))

    def test_issue46(self):
        """Example for sending an arbitrary header using SimpleXMLElement"""

        # fake connection (just to test xml_request):
        client = SoapClient(
            location="https://localhost:666/",
            namespace='http://localhost/api'
        )

        # Using WSDL, the equivalent is:
        # client['MyTestHeader'] = {'username': 'test', 'password': 'test'}

        headers = SimpleXMLElement("<Headers/>")
        my_test_header = headers.add_child("MyTestHeader")
        my_test_header['xmlns'] = "service"
        my_test_header.marshall('username', 'test')
        my_test_header.marshall('password', 'password')

        try:
            client.methodname(headers=headers)
        except:
            open("issue46.xml", "wb").write(client.xml_request)
            self.assert_('<soap:Header><MyTestHeader xmlns="service">'
                            '<username>test</username>'
                            '<password>password</password>'
                         '</MyTestHeader></soap:Header>' in client.xml_request.decode(),
                         "header not in request!")

    def test_issue47_wsdl(self):
        """Separate Header message WSDL (carizen)"""

        client = SoapClient(wsdl="https://api.clarizen.com/v1.0/Clarizen.svc")

        session = client['Session'] = {'ID': '1234'}

        try:
            client.Logout()
        except:
            open("issue47_wsdl.xml", "wb").write(client.xml_request)
            self.assert_('<soap:Header><Session>'
                            '<ID>1234</ID>'
                         '</Session></soap:Header>' in client.xml_request.decode(),
                         "Session header not in request!")

    def test_issue47_raw(self):
        """Same example (clarizen), with raw headers (no wsdl)!"""
        client = SoapClient(
            location="https://api.clarizen.com/v1.0/Clarizen.svc",
            namespace='http://clarizen.com/api'
        )

        headers = SimpleXMLElement("<Headers/>", namespace="http://clarizen.com/api",
                                   prefix="ns1")
        session = headers.add_child("Session")
        session['xmlns'] = "http://clarizen.com/api"
        session.marshall('ID', '1234')

        client.location = "https://api.clarizen.com/v1.0/Clarizen.svc"
        client.action = "http://clarizen.com/api/IClarizen/Logout"
        try:
            client.call("Logout", headers=headers)
        except:
            open("issue47_raw.xml", "wb").write(client.xml_request)
            self.assert_('<soap:Header><ns1:Session xmlns="http://clarizen.com/api">'
                            '<ID>1234</ID>'
                         '</ns1:Session></soap:Header>' in client.xml_request.decode(),
                         "Session header not in request!")

    def test_issue66(self):
        """Verify marshaled requests can be sent with no children"""
        # fake connection (just to test xml_request):
        client = SoapClient(
            location="https://localhost:666/",
            namespace='http://localhost/api'
        )

        request = SimpleXMLElement("<ChildlessRequest/>")
        try:
            client.call('ChildlessRequest', request)
        except:
            open("issue66.xml", "wb").write(client.xml_request)
            self.assert_('<ChildlessRequest' in client.xml_request.decode(),
                         "<ChildlessRequest not in request!")
            self.assert_('</ChildlessRequest>' in client.xml_request.decode(),
                         "</ChildlessRequest> not in request!")

    def test_issue69(self):
        """Boolean value not converted correctly during marshall"""
        span = SimpleXMLElement('<span><name>foo</name></span>')
        span.marshall('value', True)
        d = {'span': {'name': str, 'value': bool}}
        e = {'span': {'name': 'foo', 'value': True}}
        self.assertEqual(span.unmarshall(d), e)

    def test_issue78(self):
        """Example for sending an arbitrary header using SimpleXMLElement and WSDL"""

        # fake connection (just to test xml_request):
        client = SoapClient(
            wsdl='http://dczorgwelzijn-test.qmark.nl/qmwise4/qmwise.asmx?wsdl'
        )

        # Using WSDL, the easier form is but this doesn't allow for namespaces to be used.
        # If the server requires these (buggy server?) the dictionary method won't work
        # and marshall will not marshall 'ns:username' style keys
        # client['MyTestHeader'] = {'username': 'test', 'password': 'test'}

        namespace = 'http://questionmark.com/QMWISe/'
        ns = 'qmw'
        header = SimpleXMLElement('<Headers/>', namespace=namespace, prefix=ns)
        security = header.add_child("Security")
        security['xmlns:qmw'] = namespace
        security.marshall('ClientID', 'NAME', ns=ns)
        security.marshall('Checksum', 'PASSWORD', ns=ns)
        client['Security'] = security

        try:
            client.GetParticipantList()
        except:
            #open("issue78.xml", "wb").write(client.xml_request)
            print(client.xml_request)
            header = '<soap:Header>' \
                         '<qmw:Security xmlns:qmw="http://questionmark.com/QMWISe/">' \
                             '<qmw:ClientID>NAME</qmw:ClientID>' \
                             '<qmw:Checksum>PASSWORD</qmw:Checksum>' \
                         '</qmw:Security>' \
                     '</soap:Header>'
            xml = SimpleXMLElement(client.xml_request)
            self.assertEquals(str(xml.ClientID), "NAME")
            self.assertEquals(str(xml.Checksum), "PASSWORD")

    def test_issue89(self):
        """Setting attributes for request tag."""
        # fake connection (just to test xml_request):
        client = SoapClient(
            location="https://localhost:666/",
            namespace='http://localhost/api'
        )
        request = SimpleXMLElement(
            """<?xml version="1.0" encoding="UTF-8"?><test a="b"><a>3</a></test>"""
        ) # manually make request msg
        try:
            client.call('test', request)
        except:
            open("issue89.xml", "wb").write(client.xml_request)
            self.assert_('<test a="b" xmlns="http://localhost/api">' in client.xml_request.decode(),
                         "attribute not in request!")

    def test_issue101(self):
        """automatic relative import support"""

        client = SoapClient(wsdl="https://raw.github.com/vadimcomanescu/vmwarephp/master/library/Vmwarephp/Wsdl/vimService.wsdl")
        try:
            client.Login(parameters={'userName': 'username', 'password': 'password'})
        except IOError:
            pass
        try:
            client.Logout()
        except IOError:
            pass

    def test_issue104(self):
        """SoapClient did not build all arguments for Marketo."""
        method = 'getLead'
        args = {'leadKey': {'keyType': 'IDNUM', 'keyValue': '1'}}

        # fake connection (just to test xml_request):
        client = SoapClient(wsdl='http://app.marketo.com/soap/mktows/2_1?WSDL')
        input = client.get_operation(method)['input']

        params = ('paramsGetLead', [('leadKey', {'keyType': 'IDNUM', 'keyValue': '1'})])

        self.assertEqual(params, client.wsdl_call_get_params(method, input, args))
        self.assertEqual(params, client.wsdl_call_get_params(method, input, leadKey=args['leadKey']))

    def test_issue109(self):
        """Test multirefs and string arrays"""

        WSDL = 'http://usqcd.jlab.org/mdc-service/services/ILDGMDCService?wsdl'

        client = SoapClient(wsdl=WSDL,soap_server='axis')
        response = client.doEnsembleURIQuery("Xpath", "/markovChain", 0, -1)

        ret = response['doEnsembleURIQueryReturn']
        self.assertIsInstance(ret['numberOfResults'], int)
        self.assertIsInstance(ret['results'], list)
        self.assertIsInstance(ret['results'][0], basestring)
        self.assertIsInstance(ret['queryTime'], basestring)
        self.assertEqual(ret['statusCode'], "MDC_SUCCESS")

    def test_issue109bis(self):
        """Test string arrays not defined in the wsdl (but sent in the response)"""

        WSDL = 'http://globe-meta.ifh.de:8080/axis/services/ILDG_MDC?wsdl'

        client = SoapClient(wsdl=WSDL,soap_server='axis')
        response = client.doEnsembleURIQuery("Xpath", "/markovChain", 0, -1)

        ret = response['doEnsembleURIQueryReturn']
        self.assertIsInstance(ret['numberOfResults'], int)
        self.assertIsInstance(ret['results'], list)
        self.assertIsInstance(ret['results'][0], basestring)

    def test_issue113(self):
        """Test target namespace in wsdl import"""
        WSDL = "https://test.paymentgate.ru/testpayment/webservices/merchant-ws?wsdl"
        client = SoapClient(wsdl=WSDL)
        try:
            client.getOrderStatusExtended(order={'merchantOrderNumber':'1'})
        except SoapFault as sf:
            # ignore exception caused by missing credentials sent in this test:
            if sf.faultstring != "An error was discovered processing the <wsse:Security> header":
                raise

        # verify the correct namespace:
        xml = SimpleXMLElement(client.xml_request)
        ns_uri = xml.getOrderStatusExtended['xmlns']
        self.assertEqual(ns_uri,
                         "http://engine.paymentgate.ru/webservices/merchant")

    def test_issue105(self):
        """Test target namespace in wsdl (conflicting import)"""
        WSDL = "https://api.dc2.computing.cloud.it/WsEndUser/v2.4/WsEndUser.svc?wsdl"
        client = SoapClient(wsdl=WSDL)
        try:
            client.SetEnqueueServerStop(serverId=37)
        except SoapFault as sf:
            # ignore exception caused by missing credentials sent in this test:
            if sf.faultstring != "An error occurred when verifying security for the message.":
                raise

        # verify the correct namespace:
        xml = SimpleXMLElement(client.xml_request)
        ns_uri = xml.SetEnqueueServerStop['xmlns']
        self.assertEqual(ns_uri,
                         "https://api.computing.cloud.it/WsEndUser")

    def test_issue114(self):
        """Test no schema in wsdl (Lotus-Domino)"""
        WSDL = "http://mail.tpsgroup.ru/GateWay/WebRequests.nsf/WebRequest?WSDL"
        # WSDL= "file:WebRequest.xml"
        try:
            client = SoapClient(wsdl=WSDL, soap_server="axis")
            #print client.help("CREATEREQUEST")
            ret = client.CREATEREQUEST(LOGIN="hello", REQUESTTYPE=1, REQUESTCONTENT="test")
        except SoapFault as sf:
            # todo: check as service is returning DOM failure
            # verify the correct namespace:
            xml = SimpleXMLElement(client.xml_request)
            ns_uri = xml.CREATEREQUEST['xmlns']
            self.assertEqual(ns_uri, "http://tps.ru")

    def test_issue116(self):
        """Test string conversion and encoding of a SoapFault exception"""
        exception = SoapFault('000', u'fault stríng')
        exception_string = str(exception)
        self.assertTrue(isinstance(exception_string, str))
        if sys.version < '3':
            self.assertEqual(exception_string, '000: fault strng')
        else:
            self.assertEqual(exception_string, '000: fault stríng')



if __name__ == '__main__':
    #unittest.main()
    suite = unittest.TestSuite()
    suite.addTest(TestIssues('test_issue8_wsdl'))
    unittest.TextTestRunner().run(suite)
