#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Pythonic simple SOAP Client implementation"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.0"

try:
    import httplib2
    Http = httplib2.Http
except ImportError:
    import urllib2
    class Http(): # wrapper to use when httplib2 not available
        def request(self, url, method, body, headers):
            f = urllib2.urlopen(urllib2.Request(url, body, headers))
            return f.info(), f.read()

    
from simplexml import SimpleXMLElement, TYPE_MAP

class SoapFault(RuntimeError):
    def __init__(self,faultcode,faultstring):
        self.faultcode = faultcode
        self.faultstring = faultstring

# soap protocol specification & namespace
soap_namespaces = dict(
    soap11="http://schemas.xmlsoap.org/soap/envelope/",
    soap="http://schemas.xmlsoap.org/soap/envelope/",
    soapenv="http://schemas.xmlsoap.org/soap/envelope/",
    soap12="http://www.w3.org/2003/05/soap-env",
)

class SoapClient(object):
    "Simple SOAP Client (símil PHP)"
    def __init__(self, location = None, action = None, namespace = None,
                 cert = None, trace = False, exceptions = False, proxy = None, ns=False, 
                 soap_ns=None):
        self.certssl = cert             
        self.keyssl = None              
        self.location = location        # server location (url)
        self.action = action            # SOAP base action
        self.namespace = namespace      # message 
        self.trace = trace              # show debug messages
        self.exceptions = exceptions    # lanzar execpiones? (Soap Faults)
        self.xml_request = self.xml_response = ''
        if not soap_ns and not ns:
            self.__soap_ns = 'soap' # 1.1
        elif not soap_ns and ns:
            self.__soap_ns = 'soapenv' # 1.2
        else:
            self.__soap_ns = soap_ns

        if not proxy:
            self.http = Http()
        else:
            import socks
            ##httplib2.debuglevel=4
            self.http = httplib2.Http(proxy_info = httplib2.ProxyInfo(
                proxy_type=socks.PROXY_TYPE_HTTP, **proxy))
        #if self.certssl: # esto funciona para validar al server?
        #    self.http.add_certificate(self.keyssl, self.keyssl, self.certssl)
        self.__ns = ns # namespace prefix or False to not use it
        if not ns:
            self.__xml = """<?xml version="1.0" encoding="UTF-8"?> 
<%(soap_ns)s:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
    xmlns:%(soap_ns)s="%(soap_uri)s">
<%(soap_ns)s:Body>
    <%(method)s xmlns="%(namespace)s">
    </%(method)s>
</%(soap_ns)s:Body>
</%(soap_ns)s:Envelope>"""
        else:
            self.__xml = """<?xml version="1.0" encoding="UTF-8"?>
<%(soap_ns)s:Envelope xmlns:%(soap_ns)s="%(soap_uri)s" xmlns:%(ns)s="%(namespace)s">
<%(soap_ns)s:Header/>
<%(soap_ns)s:Body>
    <%(ns)s:%(method)s>
    </%(ns)s:%(method)s>
</%(soap_ns)s:Body>
</%(soap_ns)s:Envelope>"""

    def __getattr__(self, attr):
        "Return a pseudo-method that can be called"
        return lambda self=self, *args, **kwargs: self.call(attr,*args,**kwargs)
    
    def call(self, method, *args, **kwargs):
        "Prepare xml request and make SOAP call, returning a SimpleXMLElement"
        # Basic SOAP request:
        xml = self.__xml % dict(method=method, namespace=self.namespace, ns=self.__ns,
                                soap_ns=self.__soap_ns, soap_uri=soap_namespaces[self.__soap_ns])
        request = SimpleXMLElement(xml,namespace=self.__ns and self.namespace, prefix=self.__ns)
        # serialize parameters
        if kwargs:
            parameters = kwargs.items()
        else:
            parameters = args
        for k,v in parameters: # dict: tag=valor
            getattr(request,method).marshall(k,v)
        self.xml_request = request.as_xml()
        self.xml_response = self.send(method, self.xml_request)
        response = SimpleXMLElement(self.xml_response, namespace=self.namespace)
        if self.exceptions and ("soapenv:Fault" in response or "soap:Fault" in response):
            raise SoapFault(unicode(response.faultcode), unicode(response.faultstring))
        return response    
    
    def send(self, method, xml):
        "Send SOAP request using HTTP"
        if self.location == 'test': return
        location = "%s" % self.location #?op=%s" % (self.location, method)
        headers={
                'Content-type': 'text/xml; charset="UTF-8"',
                'Content-length': str(len(xml)),
                "SOAPAction": "\"%s%s\"" % (self.action,method)
                }
        if self.trace:
            print "-"*80
            print "POST %s" % location
            print '\n'.join(["%s: %s" % (k,v) for k,v in headers.items()])
            print u"\n%s" % xml.decode("utf8","ignore")
        response, content = self.http.request(
            location,"POST", body=xml, headers=headers )
        self.response = response
        self.content = content
        if self.trace: 
            print 
            print '\n'.join(["%s: %s" % (k,v) for k,v in response.items()])
            print content.decode("utf8","ignore")
            print "="*80
        return content

    def wsdl(self, xml):
        "Parse Web Service Description v1.1"
        soap_ns="http://schemas.xmlsoap.org/wsdl/soap/"
        wsdl_ns="http://schemas.xmlsoap.org/wsdl/"
        xsd_ns="http://www.w3.org/2001/XMLSchema"
        xsi_ns="http://www.w3.org/2001/XMLSchema-instance"

        get_local_name = lambda s: str((':' in s) and s.split(':')[1] or s)
        
        REVERSE_TYPE_MAP = dict([(v,k) for k,v in TYPE_MAP.items()])
        
        # Parse WSDL XML:
        wsdl = SimpleXMLElement(xml, namespace=wsdl_ns)
        
        # Extract useful data:
        self.namespace = wsdl['targetNamespace']
        self.documentation = str(wsdl.documentation)
        
        bindings = {}           # binding_name: binding
        operations = {}
        port_type_bindings = {} # port_type_name: binding
        messages = {}           # message:element
        elements = {}           # element: type def

        ##schema = wsdl.types('schema',ns=xsd_ns)
        for service in wsdl.service:
            service_name=service['name']
            ##self.documentation=service['documentation']
            port = service.port
            binding_name = get_local_name(port['binding'])

            bindings[binding_name] = {'service': service_name,
                'location': port('address', ns=soap_ns)['location'],
                }
             
        for binding in wsdl.binding:
            binding_name = binding['name']
            # transport can be soap 1.2, ignore (None)
            soap_binding = binding('binding', ns=soap_ns, error=False)
            transport = soap_binding and soap_binding['transport'] or None
            port_type_name = get_local_name(binding['type'])
            bindings[binding_name] = {
                'port_type_name': port_type_name,
                'transport': transport, 'operations': {},
                }
            port_type_bindings[port_type_name] = bindings[binding_name]
            for operation in binding.operation:
                op_name = operation['name']
                # operation can be soap 1.2, ignore (None)
                op = operation('operation',ns=soap_ns, error=False)
                action = op and op['soapAction'] or None
                d = operations.setdefault(op_name, {})
                bindings[binding_name]['operations'][op_name] = d
                d.update({'name': op_name, "action": action})
        
        def process_element(element_name, children):
            print "Processing element", element_name
            for tag in children:
                print tag.get_name()
                d = {}
                for e in tag.children():
                    t = e['type'].split(":")
                    if len(t)>1:
                        ns, type_name = t
                    else:
                        ns, type_name = "xsd", t[0]
                    if ns=='xsd' or ns=='s': #TODO:FIX!
                        # look for the type, None == any
                        fn = REVERSE_TYPE_MAP.get(str(type_name), None)
                    else:
                        # complex type, postprocess later
                        fn = elements.setdefault(str(type_name), {})
                    e_name = str(e['name'])
                    if e['maxOccurs']=="unbounded":
                        # it's an array...
                        d[e_name] =[fn]
                    else:
                        d[e_name] = fn
                
                elements.setdefault(element_name,{}).update(d)

        for element in wsdl.types("schema", ns=xsd_ns).children():
                element_name = str(element['name'])
                if element.get_local_name() == 'complexType':
                    children = element.children()
                else:
                    children = element.children().children()
                process_element(element_name, children)
                    
        for message in wsdl.message:
            messages[message['name']] = elements.get(get_local_name(message.part['element']), {})
        
        for port_type in wsdl.portType:
            port_type_name = port_type['name']
            binding = port_type_bindings[port_type_name]

            for operation in port_type.operation:
                op_name = operation['name']
                op = operations[op_name] 
                op['documentation'] = str(operation('documentation', error=False) or '')
                op['input'] = messages[get_local_name(operation.input['message'])]
                op['output'] = messages[get_local_name(operation.output['message'])]

        import pprint
        pprint.pprint(bindings)
        #pprint.pprint(messages)
        
def parse_proxy(proxy_str):
    "Parses proxy address user:pass@host:port into a dict suitable for httplib2"
    proxy_dict = {}
    if proxy_str is None:
        return 
    if "@" in proxy_str:
        user_pass, host_port = proxy_str.split("@")
    else:
        user_pass, host_port = "", proxy_str
    if ":" in host_port:
        host, port = host_port.split(":")
        proxy_dict['proxy_host'], proxy_dict['proxy_port'] = host, int(port)
    if ":" in user_pass:
        proxy_dict['proxy_user'], proxy_dict['proxy_pass'] = user_pass.split(":")
    return proxy_dict
    
    
if __name__=="__main__":
    import sys
    
    if '--web2py' in sys.argv:
        # test sample webservice exposed by web2py
        from client import SoapClient
        client = SoapClient(
            location = "http://127.0.0.1:8000/webservices/sample/call/soap",
            action = 'http://127.0.0.1:8000/webservices/sample/call/soap', # SOAPAction
            namespace = "http://127.0.0.1:8000/webservices/sample/call/soap", 
            soap_ns='soap',
            trace = True,
            ns = False)
        response = client.AddIntegers(a=3,b=2)
        result = response.AddResult
        print int(result)

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
        token = "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYW"
        sign = "gXVvzVwRrfkUAZKoy8ZqA3AL8IZgVxUvOHQH6g1/XzZJns1/k0lUdJslkzW"
        cuit = long(30199999)
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

    client = SoapClient()
    client.wsdl(open("C:/wsfex.wsdl").read())
    
    ##print parse_proxy(None)
    ##print parse_proxy("host:1234")
    ##print parse_proxy("user:pass@host:1234")
    ##sys.exit(0) 
