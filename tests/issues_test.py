# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import unittest
import httplib2
import socket
from xml.parsers.expat import ExpatError
from pysimplesoap.client import SoapClient, SimpleXMLElement, SoapFault
from .dummy_utils import DummyHTTP, TEST_DIR

import sys
if sys.version > '3':
    basestring = str
    unicode = str


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
        output = languages['output']['getValidLanguages13Response']
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
            str(result)

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
        self.assertEqual(unicode(res('countryCode')), "IE")
        self.assertEqual(unicode(res('vatNumber')), "6388047V")
        self.assertEqual(unicode(res('name')), "GOOGLE IRELAND LIMITED")
        self.assertEqual(unicode(res('address')), "1ST & 2ND FLOOR ,GORDON HOUSE ,"
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

        client.help("Login")
        client.help("Logout")
        client.help("Query")
        client.help("Metadata")
        client.help("Execute")

    def test_issue44(self):
        """Test namespace"""    
        client = SoapClient(wsdl="https://api.clarizen.com/v1.0/Clarizen.svc")        
        try:
            response = client.Login(userName="foo",password="bar")
        except Exception as e:
            self.assertEquals(e.faultcode, 's:InvalidUserNameOrPassword')

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

    def test_issue49(self):
        """Test netsuite wsdl"""    
        client = SoapClient(wsdl="https://webservices.netsuite.com/wsdl/v2011_2_0/netsuite.wsdl")        
        try:
            response = client.login(passport=dict(email="joe@example.com", password="secret", account='hello', role={'name': 'joe'}))
        except Exception as e:
            # It returns "This document you requested has moved temporarily."
            pass

    def test_issue57(self):
        """Test SalesForce wsdl"""
        # open the attached sfdc_enterprise_v20.wsdl to the issue in googlecode 
        client = SoapClient(wsdl="https://pysimplesoap.googlecode.com/issues/attachment?aid=570000001&name=sfdc_enterprise_v20.wsdl&token=bD6VTXMx8p4GJQHGhlQI1ISorSA%3A1399085346613")        
        try:
            response = client.login(username="john", password="doe")
        except Exception as e:
            # It returns "This document you requested has moved temporarily."
            self.assertEqual(e.faultcode, 'INVALID_LOGIN')
                     
    def test_issue60(self):
        """Verify unmarshalling of custom xsi:type="SOAPENC:Array" """
        wsdl_url = 'http://peopleask.ooz.ie/soap.wsdl' 
        client = SoapClient(wsdl=wsdl_url, soap_server="unknown", trace=False)
        questions = client.GetQuestionsAbout(query="money")
        self.assertIsInstance(questions, list)
        for question in questions:
            self.assertIsNotNone(question)
            self.assertNotEqual(question, "")

                            
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
            #print(client.xml_request)
            header = '<soap:Header>' \
                         '<qmw:Security xmlns:qmw="http://questionmark.com/QMWISe/">' \
                             '<qmw:ClientID>NAME</qmw:ClientID>' \
                             '<qmw:Checksum>PASSWORD</qmw:Checksum>' \
                         '</qmw:Security>' \
                     '</soap:Header>'
            xml = SimpleXMLElement(client.xml_request)
            self.assertEquals(str(xml.ClientID), "NAME")
            self.assertEquals(str(xml.Checksum), "PASSWORD")

    def test_issue80(self):
        """Test services.conzoom.eu/addit/ wsdl"""    
        client = SoapClient(wsdl="http://services.conzoom.eu/addit/AddItService.svc?wsdl")        
        client.help("GetValues")

    def atest_issue80(self):
        """Test Issue in sending a webservice request with soap12"""    
        client = SoapClient(wsdl="http://testserver:7007/testapp/services/testService?wsdl",
                            soap_ns='soap12', trace=False, soap_server='oracle')        
        try:
            result = client.hasRole(userId='test123', role='testview')
        except httplib2.ServerNotFoundError:
	        pass

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

    def test_issue93(self):
        """Response with <xs:schema> and <xs:any>"""
        # attached sample response to the ticket:
        xml = """
<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.
xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance
" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:wsa="http://schemas.xmlsoap
.org/ws/2004/08/addressing"><soap:Header><wsa:Action>http://smbsaas/websitepanel
/enterpriseserver/AddPackageResponse</wsa:Action><wsa:MessageID>urn:uuid:af841fc
e-4607-4e4b-910e-252d1f1857fb</wsa:MessageID><wsa:RelatesTo>urn:uuid:fea15079-42
57-424b-8da7-8c9a29ec52ce</wsa:RelatesTo><wsa:To>http://schemas.xmlsoap.org/ws/2
004/08/addressing/role/anonymous</wsa:To></soap:Header><soap:Body><AddPackageRes
ponse xmlns="http://smbsaas/websitepanel/enterpriseserver"><AddPackageResult><Re
sult>798</Result><ExceedingQuotas><xs:schema id="NewDataSet" xmlns="" xmlns:xs="
http://www.w3.org/2001/XMLSchema" xmlns:msdata="urn:schemas-microsoft-com:xml-ms
data"><xs:element name="NewDataSet" msdata:IsDataSet="true" msdata:UseCurrentLoc
ale="true"><xs:complexType><xs:choice minOccurs="0" maxOccurs="unbounded"><xs:el
ement name="Table"><xs:complexType><xs:sequence><xs:element name="QuotaID" type=
"xs:int" minOccurs="0" /><xs:element name="QuotaName" type="xs:string" minOccurs
="0" /><xs:element name="QuotaValue" type="xs:int" minOccurs="0" /></xs:sequence
></xs:complexType></xs:element></xs:choice></xs:complexType></xs:element></xs:sc
hema><diffgr:diffgram xmlns:msdata="urn:schemas-microsoft-com:xml-msdata" xmlns:
diffgr="urn:schemas-microsoft-com:xml-diffgram-v1" /></ExceedingQuotas></AddPack
ageResult></AddPackageResponse></soap:Body></soap:Envelope>
"""
        xml = xml.replace("\n","").replace("\r","")
        # parse the wsdl attached to the ticket
        client = SoapClient(wsdl="https://pysimplesoap.googlecode.com/issues/attachment?aid=930004001&name=wsdl.txt&token=MIcIgTXvGmzpfFgLM-noYLehzwU%3A1399083528469", trace=False)        
        # put the sample response (no call to the real webservice is made...)
        client.http = DummyHTTP(xml)
        result = client.AddPackage(657, 33, 'Services', 'Comment', 1, datetime.datetime.now())
        # check unmarshalled results:
        self.assertEquals(result['AddPackageResult']['Result'], 798)
        # the schema is also returned as a SimpleXMLElement object (unmarshalled), get the xml:
        self.assertEquals(repr(result['AddPackageResult']['ExceedingQuotas']['schema']['element']),
            '<xs:element msdata:IsDataSet="true" msdata:UseCurrentLocale="true" name="NewDataSet"><xs:complexType><xs:choice maxOccurs="unbounded" minOccurs="0"><xs:element name="Table"><xs:complexType><xs:sequence><xs:element minOccurs="0" name="QuotaID" type="xs:int"/><xs:element minOccurs="0" name="QuotaName" type="xs:string"/><xs:element minOccurs="0" name="QuotaValue" type="xs:int"/></xs:sequence></xs:complexType></xs:element></xs:choice></xs:complexType></xs:element>')
        # the any is also returned as a SimpleXMLElement object (unmarshalled)
        self.assertEquals(str(result['AddPackageResult']['ExceedingQuotas']['diffgram']), '')

    def test_issue94(self):
        """Test wather forecast web service."""
        client = SoapClient(wsdl='http://www.restfulwebservices.net/wcf/WeatherForecastService.svc?wsdl')
        ret = client.GetCitiesByCountry('korea')
        for d in ret['GetCitiesByCountryResult']:
            #print d['string']
            self.assertEquals(d.keys()[0], 'string')
        self.assertEquals(len(ret['GetCitiesByCountryResult']), 53)
        self.assertEquals(len(ret['GetCitiesByCountryResult'][0]), 1)
        self.assertEquals(ret['GetCitiesByCountryResult'][0]['string'], 'KWANGJU')

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

        self.assertEqual(params, client.wsdl_call_get_params(method, input, [args], {}))
        self.assertEqual(params, client.wsdl_call_get_params(method, input, [], dict(leadKey=args['leadKey'])))

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
        WSDL = "https://pysimplesoap.googlecode.com/issues/attachment?aid=1140000000&name=WebRequest.xml&token=QVf8DlJ1qmKRH8LAbU4eSe2Ban0%3A1399084258723"
        # WSDL= "file:WebRequest.xml"
        try:
            client = SoapClient(wsdl=WSDL, soap_server="axis")
            #print client.help("CREATEREQUEST")
            ret = client.CREATEREQUEST(LOGIN="hello", REQUESTTYPE=1, REQUESTCONTENT="test")
        except ExpatError:
            # the service seems to be expecting basic auth
            pass
        except SoapFault as sf:
            # todo: check as service is returning DOM failure
            # verify the correct namespace:
            xml = SimpleXMLElement(client.xml_request)
            ns_uri = xml.CREATEREQUEST['xmlns']
            self.assertEqual(ns_uri, "http://tps.ru")

    def test_issue116(self):
        """Test string conversion and encoding of a SoapFault exception"""
        exception = SoapFault('000', 'fault stríng')
        exception_string = str(exception)
        self.assertTrue(isinstance(exception_string, str))
        if sys.version < '3':
            self.assertEqual(exception_string, '000: fault strng')
        else:
            self.assertEqual(exception_string, '000: fault stríng')

    def test_issue122(self):
        """Test multiple separate messages in input header"""
        APIURL = "https://ecommercetest.collector.se/v3.0/InvoiceServiceV31.svc?singleWsdl"
        client = SoapClient(wsdl=APIURL)

        # set headers (first two were not correctly handled
        client['Username'] = 'user'
        client['Password'] = 'pass'
        client['ClientIpAddress'] = '127.0.0.1'

        variables = {
            "CountryCode": "SE",
            "RegNo": "1234567890",
        }

        expected_xml = ("<soap:Header>"
                        "<Username>user</Username>"
                        "<Password>pass</Password>"
                        "<ClientIpAddress>127.0.0.1</ClientIpAddress>"
                        "</soap:Header>")
        try:
            response = client.GetAddress(**variables)
        except SoapFault:
            self.assertIn(expected_xml, client.xml_request)

    def test_issue123(self):
        """Basic test for WSDL lacking service tag """
        wsdl = "http://www.onvif.org/onvif/ver10/device/wsdl/devicemgmt.wsdl"
        client = SoapClient(wsdl=wsdl)
        # this could cause infinite recursion (TODO: investigate)
        #client.help("CreateUsers")
        #client.help("GetServices")
        # this is not a real webservice (just specification) catch HTTP error
        try: 
            client.GetServices(IncludeCapability=True)
        except Exception as e:
            self.assertEqual(str(e), "RelativeURIError: Only absolute URIs are allowed. uri = ")

    def test_issue127(self):
        """Test relative schema locations in imports"""
        client = SoapClient(wsdl = 'https://eisoukr.musala.com:9443/IrmInboundMediationWeb/sca/MTPLPolicyWSExport/WEB-INF/wsdl/wsdl/IrmInboundMediation_MTPLPolicyWSExport.wsdl')
        try:
            resp = client.voidMTPLPolicy()
        except Exception as e:
            self.assertIn('InvalidSecurity', e.faultcode)

    def test_issue128(self):
        ""
        client = SoapClient(
                wsdl = "https://apiapac.lumesse-talenthub.com/HRIS/SOAP/Candidate?WSDL",
                location = "https://apiapac.lumesse-talenthub.com/HRIS/SOAP/Candidate?api_key=azhmc6m8sq2gf2jqwywa37g4",
                ns = True
                )
        # basic test as no test case was provided
        try:
            resp = client.getContracts()
        except:
            self.assertEqual(client.xml_response, '<h1>Gateway Timeout</h1>')

    def test_issue129(self):
        """Test RPC style (axis) messages (including parameter order)"""
        wsdl_url = 'file:tests/data/teca_server_wsdl.xml'
        client = SoapClient(wsdl=wsdl_url, soap_server='axis')
        client.help("contaVolumi")
        response = client.contaVolumi(user_id=1234, valoreIndice=["IDENTIFIER", ""])
        self.assertEqual(response, {'contaVolumiReturn': 0})

    def test_issue130(self):
        """Test complex Array (axis) """
        wsdl_url = 'file:tests/data/teca_server_wsdl.xml'
        client = SoapClient(wsdl=wsdl_url, soap_server='axis', trace=False)
        #print client.help("find")
        #response = client.find(25, ['SUBJECT', 'Ethos'], 10, 0)
        port = client.services[u'WsTecaServerService']['ports']['tecaServer']
        op = port['operations']['find']
        out = op['output']['findResponse']['findReturn']
        # findReturn should be a list of Contenitore
        self.assertIsInstance(out, list)
        element = out[0]['Contenitore']
        for key in [u'EMail', u'bloccato', u'classe', u'codice', u'creatoDa', 
                    u'creatoIl', u'dbName', u'dbPort', u'dbUrl', u'username']:
            self.assertIn(key, element)
        # valoriDigitali should be a list of anyType (None)
        self.assertIsInstance(element[u'valoriDigitali'], list)
        self.assertIsNone(element[u'valoriDigitali'][0])

    def test_issue139(self):
        """Test MKS wsdl (extension)"""
        # open the attached Integrity_10_2Service to the issue in googlecode 
        client = SoapClient(wsdl="https://pysimplesoap.googlecode.com/issues/attachment?aid=1390000000&name=Integrity_10_2.wsdl&token=3VG47As2K-EupP9GgotYckgb0Bc%3A1399064656814")
        #print client.help("getItemsByCustomQuery")
        try:
            response = client.getItemsByCustomQuery(arg0={'Username': 'user', 'Password' : 'pass', 'InputField' : 'ID', 'QueryDefinition' : 'query'})
        except httplib2.ServerNotFoundError:
	        pass

    def test_issue141(self):
        """Test voxone VoxAPI wsdl (ref element)"""
        import datetime
        import hmac
        import hashlib

        client = SoapClient(wsdl="http://sandbox.voxbone.com/VoxAPI/services/VoxAPI?wsdl", cache=None)
        client.help("GetPOPList")

        key = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f000000")
        password="fwefewfewfew"
        usertoken={'Username': "oihfweohf", 'Key': key, 'Hash': hmac.new(key, password, digestmod=hashlib.sha1).hexdigest()}
        try:
            response = client.GetPOPList(UserToken=usertoken)
            result = response['GetPOPListResponse']
        except SoapFault as sf:
            # ignore exception caused by missing credentials sent in this test:
            if sf.faultstring != "Either your username or password is invalid":
                raise

    def test_issue143(self):
        """Test webservice.vso.dunes.ch wsdl (array sub-element)"""
        wsdl_url = 'file:tests/data/vco.wsdl' 
        try:
            vcoWS = SoapClient(wsdl=wsdl_url, soap_server="axis", trace=False)
            workflowInputs = [{'name': 'vmName', 'type': 'string', 'value': 'VMNAME'}]
            workflowToken = vcoWS.executeWorkflow(workflowId='my_uuid', username="my_user", password="my_password", workflowInputs=workflowInputs)
        except httplib2.ServerNotFoundError:
            #import pdb;pdb.set_trace()
            print vcoWS.xml_response
            pass

    def test_issue157(self):
        """Test WSDL types "top level" import for .NET WCF"""
        wsdl = "https://sdkstage.microbilt.com/WebServices/Ex/ExStd.svc?wsdl"
        client = SoapClient(wsdl=wsdl, trace=False)
        # method call, should not fail, but doesn't return anything useful:
        client.Map(bureauResponse=1234)     
        # in case of issue, it will throw the following exceptions:
        # AttributeError: Tag not found: schema (No elements found)
        # ValueError: Invalid Args Structure


if __name__ == '__main__':
    #unittest.main()
    suite = unittest.TestSuite()
    #suite.addTest(TestIssues('test_issue34'))
    #suite.addTest(TestIssues('test_issue93'))
    #suite.addTest(TestIssues('test_issue57'))
    #suite.addTest(TestIssues('test_issue60'))
    #suite.addTest(TestIssues('test_issue80'))
    #suite.addTest(TestIssues('test_issue101'))
    #suite.addTest(TestIssues('test_issue114'))
    #suite.addTest(TestIssues('test_issue123'))
    #suite.addTest(TestIssues('test_issue127'))
    #suite.addTest(TestIssues('test_issue130'))
    #suite.addTest(TestIssues('test_issue141'))
    #suite.addTest(TestIssues('test_issue143'))
    suite.addTest(TestIssues('test_issue157'))
    unittest.TextTestRunner().run(suite)
