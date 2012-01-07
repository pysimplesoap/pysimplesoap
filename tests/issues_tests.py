import unittest
from pysimplesoap.client import SoapClient, SoapFault

class TestIssues(unittest.TestCase):

    def test_issue19(self):
        "Test xsd namespace found under schema elementes"
        client = SoapClient(wsdl='http://www.destin8.co.uk/ISLInterface/ISLInterface?WSDL')

    def test_issue34(self):
        "Test soap_server SoapClient constructor parameter"
        client = SoapClient(wsdl="http://eklima.met.no/metdata/MetDataService?WSDL", soap_server="oracle", trace=True, cache=None)
        ##print client.help("getStationsProperties")
        ##print client.help("getValidLanguages")

        # fix bad wsdl: server returns "getValidLanguagesResponse" instead of "getValidLanguages12Response"
        output = client.services['MetDataService']['ports']['MetDataServicePort']['operations']['getValidLanguages']['output']['getValidLanguages12Response']
        client.services['MetDataService']['ports']['MetDataServicePort']['operations']['getValidLanguages']['output'] = {'getValidLanguagesResponse': output}

        lang = client.getValidLanguages()

        self.assertEqual(lang, {'return': [{'item': u'no'},{'item': u'en'}, {'item': u'ny'}]})

    def test_issue35_raw(self):    

        url = 'http://wennekers.epcc.ed.ac.uk:8080/axis/services/MetadataCatalogue'
        client = SoapClient(location=url,action="", trace=False)
        response = client.call("doEnsembleURIQuery", ("queryFormat", "Xpath"), ("queryString", "/markovChain"), ("startIndex", 0), ("maxResults", -1))
        self.assertEqual(str(response.statusCode), "MDC_INVALID_REQUEST")
        #print str(response.queryTime)
        self.assertEqual(int(response.totalResults), 0)
        self.assertEqual(int(response.startIndex), 0)
        self.assertEqual(int(response.numberOfResults), 0)

        for result in response.results:
            print str(result)

    def test_issue35_wsdl(self):
        "Test positional parameters, multiRefs and axis messages"
    
        url = 'http://wennekers.epcc.ed.ac.uk:8080/axis/services/MetadataCatalogue?WSDL'
        client = SoapClient(wsdl=url,trace=False, soap_server="axis")
        response = client.doEnsembleURIQuery(queryFormat="Xpath", queryString="/markovChain", startIndex=0, maxResults=-1)

        ret = response['doEnsembleURIQueryReturn']
        self.assertEqual(ret['statusCode'], "MDC_INVALID_REQUEST")
        self.assertEqual(ret['totalResults'], 0)
        self.assertEqual(ret['startIndex'], 0)
        self.assertEqual(ret['numberOfResults'], 0)


    def test_issue8(self):
        "Test europa.eu tax service (WSDL namespace)"

        VIES_URL='http://ec.europa.eu/taxation_customs/vies/services/checkVatService.wsdl'

        client = SoapClient(
                    location = "http://ec.europa.eu/taxation_customs/vies/services/checkVatService",
                    action = '', # SOAPAction
                    namespace = "urn:ec.europa.eu:taxud:vies:services:checkVat:types",
                    trace = False
                    )
        vat = 'BE0897290877'
        code = vat[:2]
        number = vat[2:]
        res = client.checkVat(countryCode=code, vatNumber=number)
        self.assertEqual(str(res('countryCode')), "BE")
        self.assertEqual(str(res('vatNumber')), "0897290877")
        self.assertEqual(str(res('name')), "SPRL B2CK")
        self.assertEqual(str(res('address')), "RUE DE ROTTERDAM 4 B21\n4000  LIEGE")

    ##def test_ups(self):
    ##    "Test UPS tracking service"
    ##    WSDL = "file:ups.wsdl"
    ##    client = SoapClient(wsdl=WSDL, ns="web", trace=True)
    ##    print client.help("ProcessTrack")

        
if __name__ == '__main__':
    test_issue35()
    unittest.main()
    
