#!/usr/bin/python
# -*- coding: latin-1 -*-
  
    
if __name__=="__main__":
    import sys
    
    if '--web2py' in sys.argv:
        # test local sample webservice exposed by web2py
        from client import SoapClient
        if not '--wsdl' in sys.argv:
            client = SoapClient(
                location = "http://127.0.0.1:8000/webservices/sample/call/soap",
                action = 'http://127.0.0.1:8000/webservices/sample/call/soap', # SOAPAction
                namespace = "http://127.0.0.1:8000/webservices/sample/call/soap", 
                soap_ns='soap', trace = True, ns = False, exceptions=True)
        else:
            client = SoapClient(wsdl="http://127.0.0.1:8000/webservices/sample/call/soap?WSDL",trace=True)
        response = client.Dummy()
        print 'dummy', response
        response = client.Echo(value='hola')
        print 'echo', repr(response)
        response = client.AddIntegers(a=1,b=2)
        if not '--wsdl' in sys.argv:
            result = response.AddResult # manully convert returned type
            print int(result)
        else:
            result = response['AddResult']
            print result, type(result), "auto-unmarshalled"

    if '--raw' in sys.argv:
        # raw (unmarshalled parameter) local sample webservice exposed by web2py
        from client import SoapClient
        client = SoapClient(
            location = "http://127.0.0.1:8000/webservices/sample/call/soap",
            action = 'http://127.0.0.1:8000/webservices/sample/call/soap', # SOAPAction
            namespace = "http://127.0.0.1:8000/webservices/sample/call/soap", 
            soap_ns='soap', trace = True, ns = False)
        params = SimpleXMLElement("""<?xml version="1.0" encoding="UTF-8"?><AddIntegers><a>3</a><b>2</b></AddIntegers>""") # manully convert returned type
        response = client.call('AddIntegers',params)
        result = response.AddResult 
        print int(result) # manully convert returned type
            
    if '--ctg' in sys.argv:
        # test AFIP Agriculture webservice
        client = SoapClient(
            location = "https://fwshomo.afip.gov.ar/wsctg/services/CTGService",
            action = 'http://impl.service.wsctg.afip.gov.ar/CTGService/', # SOAPAction
            namespace = "http://impl.service.wsctg.afip.gov.ar/CTGService/",
            trace = True,
            ns = True)
        response = client.dummy()
        result = response.dummyResponse
        print str(result.appserver)
        print str(result.dbserver)
        print str(result.authserver)
    
    if '--wsfe' in sys.argv:
        # Demo & Test (AFIP Electronic Invoice):
        ta_string=open("TA.xml").read()   # read access ticket (wsaa.py)
        ta = SimpleXMLElement(ta_string)
        token = str(ta.credentials.token)
        sign = str(ta.credentials.sign)
        cuit = long(20267565393)
        id = 1234
        cbte =199
        client = SoapClient(
            location = "https://wswhomo.afip.gov.ar/wsfe/service.asmx",
            action = 'http://ar.gov.afip.dif.facturaelectronica/', # SOAPAction
            namespace = "http://ar.gov.afip.dif.facturaelectronica/",
            trace = True)
        results = client.FERecuperaQTYRequest(
            argAuth= {"Token": token, "Sign": sign, "cuit":long(cuit)}
        )
        if int(results.FERecuperaQTYRequestResult.RError.percode) != 0:
            print "Percode: %s" % results.FERecuperaQTYRequestResult.RError.percode
            print "MSGerror: %s" % results.FERecuperaQTYRequestResult.RError.perrmsg
        else:
            print int(results.FERecuperaQTYRequestResult.qty.value)
    
    if '--feriados' in sys.argv:
        # Demo & Test: Argentina Holidays (Ministerio del Interior):
        # this webservice seems disabled
        from datetime import datetime, timedelta
        client = SoapClient(
            location = "http://webservices.mininterior.gov.ar/Feriados/Service.svc",
            action = 'http://tempuri.org/IMyService/', # SOAPAction
            namespace = "http://tempuri.org/FeriadoDS.xsd",
            trace = True)
        dt1 = datetime.today() - timedelta(days=60)
        dt2 = datetime.today() + timedelta(days=60)
        feriadosXML = client.FeriadosEntreFechasas_xml(dt1=dt1.isoformat(), dt2=dt2.isoformat());
        print feriadosXML

    if '--wsdl-parse' in sys.argv:
        if '--proxy' in sys.argv:
            proxy = parse_proxy("localhost:8000")
        else:
            proxy = None
        if '--wrapper' in sys.argv:
            set_http_wrapper("pycurl")
        client = SoapClient(proxy=proxy)
        # Test PySimpleSOAP WSDL
        ##client.wsdl("file:C:/test.wsdl", debug=True)
        # Test Java Axis WSDL:
        client.wsdl_parse('https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl',debug=True)
        # Test .NET 2.0 WSDL:
        client.wsdl_parse('https://wswhomo.afip.gov.ar/wsfe/service.asmx?WSDL',debug=True)
        client.wsdl_parse('https://wswhomo.afip.gov.ar/wsfex/service.asmx?WSDL',debug=True)
        client.wsdl_parse('https://testdia.afip.gov.ar/Dia/Ws/wDigDepFiel/wDigDepFiel.asmx?WSDL',debug=True)
        client.services = client.wsdl_parse('https://wswhomo.afip.gov.ar/wsfexv1/service.asmx?WSDL',debug=True)
        print client.help("FEXGetCMP")
        # Test JBoss WSDL:
        client.wsdl_parse('https://fwshomo.afip.gov.ar/wsctg/services/CTGService?wsdl',debug=True)
        client.wsdl_parse('https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl',debug=True)

    if '--wsdl-client' in sys.argv:
        import time
        t0 = time.time()
        for i in range(100):
            print i
            client = SoapClient(wsdl='https://wswhomo.afip.gov.ar/wsfex/service.asmx?WSDL',cache="cache", trace=False)
            #results = client.FEXDummy()
            #print results['FEXDummyResult']['AppServer']
            #print results['FEXDummyResult']['DbServer']
            #print results['FEXDummyResult']['AuthServer']
        t1 = time.time()
        print "Total time", t1-t0

    if '--wsdl-client' in sys.argv:
        ta_string=open("TA.xml").read()   # read access ticket (wsaa.py)
        ta = SimpleXMLElement(ta_string)
        token = str(ta.credentials.token)
        sign = str(ta.credentials.sign)
        response = client.FEXGetCMP(
            Auth={"Token": token, "Sign": sign, "Cuit": 20267565393},
            Cmp={"Tipo_cbte": 19, "Punto_vta": 1, "Cbte_nro": 1}) 
        result = response['FEXGetCMPResult']
        if False: print result
        if 'FEXErr' in result:
            print "FEXError:", result['FEXErr']['ErrCode'], result['FEXErr']['ErrCode'] 
        cbt = result['FEXResultGet']
        print cbt['Cae']
        FEX_event = result['FEXEvents']
        print FEX_event['EventCode'], FEX_event['EventMsg']

    if '--wsdl-ctg' in sys.argv:
        client = SoapClient(wsdl='https://fwshomo.afip.gov.ar/wsctg/services/CTGService?wsdl',
                            trace=True, ns = "ctg")
        results = client.dummy()
        print results
        print results['DummyResponse']['appserver']
        print results['DummyResponse']['dbserver']
        print results['DummyResponse']['authserver']
        ta_string=open("TA.xml").read()   # read access ticket (wsaa.py)
        ta = SimpleXMLElement(ta_string)
        token = str(ta.credentials.token)
        sign = str(ta.credentials.sign)
        print client.help("obtenerProvincias")
        response = client.obtenerProvincias(auth={"token":token, "sign":sign, "cuitRepresentado":20267565393})
        print "response=",response
        for ret in response:
            print ret['return']['codigoProvincia'], ret['return']['descripcionProvincia'].encode("latin1")
        prueba = dict(numeroCartaDePorte=512345678, codigoEspecie=23,
                cuitRemitenteComercial=20267565393, cuitDestino=20267565393, cuitDestinatario=20267565393, 
                codigoLocalidadOrigen=3058, codigoLocalidadDestino=3059, 
                codigoCosecha='0910', pesoNetoCarga=1000, cantHoras=1, 
                patenteVehiculo='CZO985', cuitTransportista=20267565393,
                numeroCTG="43816783", transaccion='10000001681', observaciones='',
            )

        response = client.solicitarCTG( 
            auth={"token": token, "sign": sign, "cuitRepresentado": 20267565393},
            solicitarCTGRequest= prueba)

        print response['return']['numeroCTG']

    if '--libtest' in sys.argv:
        import time
        results = {}
        for lib in 'httplib2', 'urllib2', 'pycurl':
            print "testing library", lib
            set_http_wrapper(lib)
            print Http._wrapper_version
            for proxy in None, parse_proxy("localhost:8000"):
                print "proxy", proxy
                try:
                    client = SoapClient(wsdl='https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL',
                                        cache="cache", trace=False, proxy=proxy)
                    t0 = time.time()
                    print "starting...",
                    for i in range(20):
                        print i,
                        client.FEDummy()
                    t1 = time.time()
                    result = t1-t0
                except Exception, e:
                    result = "Failed: %s" % str(e)
                print "Total time", result
                results.setdefault(lib, {})[proxy and 'proxy' or 'direct'] = result
        print "\nResults:"
        for k, v in results.items():
            for k2, v2 in v.items():
                print k, k2, v2

