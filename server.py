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

"Simple SOAP Server implementation"

# WARNING: EXPERIMENTAL PROOF-OF-CONCEPT IN EARLY DEVELOPMENT STAGE 
# TODO:
# * Refactory: cleanup and remove duplicates between server ad client 
# * Generalize harcoded code
# * Handle and Enforce SoapAction, namespaces, and exceptions
# * Generate a WSDL suitable for testing with SoapUI

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "0.02"

from simplexml import SimpleXMLElement

DEBUG = False

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

class SoapDispatcher(object):
    "Simple Dispatcher for SOAP Server"
    
    def __init__(self, soap_ns='soap11', namespace=None, prefix=False, **kwargs):
        self.methods = {}
        self.soap_ns = soap_ns
        self.soap_uri = soap_namespaces[soap_ns] # soap napespace
        self.namespace = namespace
        self.prefix = prefix
    
    def register_function(self, method, function, returns, args):
        self.methods[method] = function, returns, args
        
    def dispatch(self, xml):
        "Receive and proccess SOAP call"
        request = SimpleXMLElement(xml, namespace=self.namespace)
        
        # parse request message and get local method
        method = request['soap:Body'].children()[0]
        if DEBUG: print "dispatch method", method.getName()
        function, returns_types, args_types = self.methods[method.getName()]
    
        # de-serialize parameters
        args = method.children().unmarshall(args_types)
 
        # execute function
        ret = function(**args)
        if DEBUG: print ret
        
        # build response message
        xml = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body><%(method)sResponse xmlns="%(namespace)s"/></soap:Body>
</soap:Envelope>"""  % {'method':method.getName(), 'namespace':self.namespace}
        response = SimpleXMLElement(xml, namespace=self.namespace)   

        # serialize returned values (response)
        response['%sResponse' % method.getName()].marshall(returns_types.keys()[0], ret)
        
        return response.asXML()

    # Introspection functions:

    def list_methods(self):
        "Return a list of aregistered operations"
        return [(method, function.__doc__) for method, (function, returns, args) in self.methods.items()] 

    def help(self, method=None):
        "Generate sample request and response messages"
        (function, returns, args) = self.methods[method]
        xml = """
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body><%(method)s xmlns="%(namespace)s"/></soap:Body>
</soap:Envelope>"""  % {'method':method, 'namespace':self.namespace}
        request = SimpleXMLElement(xml, namespace=self.namespace, prefix=self.prefix)
        for k,v in args.items():
            request[method].marshall(k, v, add_comments=True, ns=False)

        xml = """
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body><%(method)sResponse xmlns="%(namespace)s"/></soap:Body>
</soap:Envelope>"""  % {'method':method, 'namespace':self.namespace}
        response = SimpleXMLElement(xml, namespace=self.namespace, prefix=self.prefix)
        for k,v in returns.items():
            response['%sResponse'%method].marshall(k, v, add_comments=True, ns=False)

        return request.asXML(pretty=True), response.asXML(pretty=True), function.__doc__


    def wsdl(self):
        "Generate Web Service Description v1.1"
        xml = """<?xml version="1.0"?>
<definitions name="StockQuote" targetNamespace="http://example.com/sample.wsdl"
          xmlns:tns="http://example.com/sample.wsdl"
          xmlns:xsd1="http://example.com/sample.xsd"
          xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
          xmlns="http://schemas.xmlsoap.org/wsdl/">

    <types>
       <schema targetNamespace="http://example.com/stockquote.wsdl"
              elementFormDefault="qualified"
              xmlns="http://www.w3.org/2000/10/XMLSchema">
       </schema>
    </types>

</definitions>
"""
        wsdl = SimpleXMLElement(xml)

        for method, (function, returns, args) in self.methods.items():
            # create elements:
                
            def parseElement(name, values, array=True):
                element = wsdl['types']['schema'].addChild('element')
                element.addAttribute('name', name)
                complex = element.addChild("complexType")
                if not array:
                    all = complex.addChild("all")
                else:
                    all = complex.addChild("sequence")
                for k,v in values:
                    e = all.addChild("element")
                    e.addAttribute('name', k)
                    if array:
                        e.addAttribute('minOccurs',"0")
                        e.addAttribute('maxOccurs',"1")
                    if v in (int, str, float, bool, unicode):
                        type_map={str:'string',bool:'boolean',int:'integer',float:'float',unicode:'string'}
                        t=type_map[v]
                    elif isinstance(v, list):
                        n="tns:ArrayOf%s%s" % (name, k)
                        l = []
                        for d in v:
                            l.extend(d.items())
                        parseElement(n, l, array=True)
                        t = n
                    elif isinstance(v, dict): 
                        n="tns:%s%s" % (name, k)
                        parseElement(n, v.items())
                        t = n
                    e.addAttribute('type', t)
            
            parseElement("%sRequest" % method, args.items())
            parseElement("%sResponse" % method, returns.items())

            # create messages:
            for m,e in ('Input','Request'), ('Output','Response'):
                message = wsdl.addChild('message')
                message.addAttribute('name', "%s%s" % (method, m))
                part = message.addChild("part")
                part.addAttribute('name', 'body')
                part.addAttribute('element', 'tns:%s%s' % (method,e))

        # create ports
        portType = wsdl.addChild('portType')
        portType.addAttribute('name', "StockQuotePortType")
        for method in self.methods.keys():
            op = portType.addChild('operation')
            op.addAttribute('name', method)
            input = op.addChild("input")
            input.addAttribute('message', "tns:%sInput" % method)
            output = op.addChild("input")
            output.addAttribute('message', "tns:%sOutput" % method)

        # create bindings
        binding = wsdl.addChild('binding')
        binding.addAttribute('name', "StockQuoteSoapBinding")
        binding.addAttribute('type', "tns:StockQuotePortType")
        soapbinding= binding.addChild('soap:binding')
        soapbinding.addAttribute('style',"document")
        soapbinding.addAttribute('transport',"http://schemas.xmlsoap.org/soap/http")
        for method in self.methods.keys():
            op = binding.addChild('operation')
            op.addAttribute('name', method)
            soapop = binding.addChild('soap:operation')
            soapop.addAttribute('soapAction', "http://example.com/GetLastTradePrice")
            input = op.addChild("input")
            soapbody = input.addChild("soap:body")
            soapbody.addAttribute("use","literal")
            output = op.addChild("input")
            soapbody = output.addChild("soap:body")
            soapbody.addAttribute("use","literal")

        service = wsdl.addChild('service')
        service.addAttribute("name", "StockQuoteService")
        service.addChild('documentation', text="my first web service")
        port=service.addChild('port')
        port.addAttribute("name","StockQuotePort")
        port.addAttribute("binding","tns:StockQuoteBinding")
        soapaddress = port.addChild('soap:address')
        soapaddress.addAttribute("location","http://example.com/stockquote")
        return wsdl.asXML(pretty=True)
    

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
class SOAPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        "User viewable help information and wsdl"
        args = self.path[1:].split("?")
        print "serving", args
        if self.path != "/" and args[0] not in self.server.dispatcher.methods.keys():
            self.send_error(404, "Method not found: %s" % args[0])
        else:
            if self.path == "/":
                # return wsdl if no method supplied
                response = self.server.dispatcher.wsdl()
            else:
                # return supplied method help (?request or ?response messages)
                req, res, doc = self.server.dispatcher.help(args[0])
                if len(args)==1 or args[1]=="request":
                    response = req
                else:
                    response = res                
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.end_headers()
            self.wfile.write(response)

    def do_POST(self):
        "SOAP POST gateway"
        self.send_response(200)
        self.send_header("Content-type", "text/xml")
        self.end_headers()
        request = self.rfile.read(int(self.headers.getheader('content-length')))
        response = self.server.dispatcher.dispatch(request)
        self.wfile.write(response)


if __name__=="__main__":
    import sys

    dispatcher = SoapDispatcher(
        location = "http://localhost:8008/",
        action = 'http://localhost:8008/', # SOAPAction
        namespace = "http://example.com/sample.wsdl", prefix="ns0",
        trace = True,
        ns = True)
    
    def adder(p,c):
        print c[0]['d'],c[1]['d'],
        return {'ab': p['a']+p['b'], 'dd': c[0]['d']+c[1]['d']}
    
    dispatcher.register_function('Adder', adder,
        returns={'AddResult': {'ab': int, 'dd': str } }, 
        args={'p': {'a': int,'b': int}, 'c': [{'d':str}]})

    if '--local' in sys.argv:
        # dummy local test
        xml = """<?xml version="1.0" encoding="UTF-8"?> 
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
       <soap:Body>
         <adder xmlns="http://example.com/sample.wsdl">
           <p>
            <a>1</a>
            <b>2</b>
           </p>
           <c>
            <d>hola</d>
            <d>chau</d>
           </c>
        </adder>
       </soap:Body>
    </soap:Envelope>"""

        print dispatcher.dispatch(xml)

        for method, doc in dispatcher.list_methods():
            request, response, doc = dispatcher.help(method)
            print request
            print response
            
        print dispatcher.wsdl()

    if '--serve' in sys.argv:
        print "Starting server..."
        httpd = HTTPServer(("", 8008), SOAPHandler)
        httpd.dispatcher = dispatcher
        httpd.serve_forever()

    if '--consume' in sys.argv:
        from client import SoapClient
        client = SoapClient(
            location = "http://localhost:8008/",
            action = 'http://localhost:8008/', # SOAPAction
            namespace = "http://example.com/sample.wsdl", 
            soap_ns='soap',
            trace = True,
            ns = False)
        response = client.Adder(p={'a':1,'b':2},c=[{'d':'hola'},{'d':'chau'}])
        result = response.AddResult
        print int(result.ab)
        print str(result.dd)


