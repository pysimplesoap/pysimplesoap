#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Pythonic simple SOAP Client implementation"""

from __future__ import unicode_literals
try:
    import cPickle as pickle
except ImportError:
    import pickle
import hashlib
import logging
import os
import tempfile

from . import __author__, __copyright__, __license__, __version__, TIMEOUT
from .simplexml import SimpleXMLElement, TYPE_MAP, REVERSE_TYPE_MAP, OrderedDict
from .transport import get_http_wrapper, set_http_wrapper, get_Http
# Utility functions used throughout wsdl_parse, moved aside for readability
from .helpers import fetch, sort_dict, make_key, process_element, postprocess_element, get_message, preprocess_schema

log = logging.getLogger(__name__)


class SoapFault(RuntimeError):
    def __init__(self, faultcode, faultstring):
        self.faultcode = faultcode
        self.faultstring = faultstring
        RuntimeError.__init__(self, faultcode, faultstring)

    def __str__(self):
        return self.__unicode__().encode("ascii", "ignore")

    def __unicode__(self):
        return '%s: %s' % (self.faultcode, self.faultstring)

    def __repr__(self):
        return "SoapFault(%s, %s)" % (repr(self.faultcode),
                                      repr(self.faultstring))


# soap protocol specification & namespace
soap_namespaces = dict(
    soap11="http://schemas.xmlsoap.org/soap/envelope/",
    soap="http://schemas.xmlsoap.org/soap/envelope/",
    soapenv="http://schemas.xmlsoap.org/soap/envelope/",
    soap12="http://www.w3.org/2003/05/soap-env",
)

_USE_GLOBAL_DEFAULT = object()


class SoapClient(object):
    """Simple SOAP Client (simil PHP)"""
    def __init__(self, location=None, action=None, namespace=None,
                 cert=None, exceptions=True, proxy=None, ns=False,
                 soap_ns=None, wsdl=None, wsdl_basedir='', cache=False, cacert=None,
                 sessions=False, soap_server=None, timeout=_USE_GLOBAL_DEFAULT,
                 http_headers={}
                 ):
        """
        :param http_headers: Additional HTTP Headers; example: {'Host': 'ipsec.example.com'}
        """
        self.certssl = cert
        self.keyssl = None
        self.location = location        # server location (url)
        self.action = action            # SOAP base action
        self.namespace = namespace      # message
        self.exceptions = exceptions    # lanzar execpiones? (Soap Faults)
        self.xml_request = self.xml_response = ''
        self.http_headers = http_headers
        self.wsdl_basedir = wsdl_basedir
        if not soap_ns and not ns:
            self.__soap_ns = 'soap'  # 1.1
        elif not soap_ns and ns:
            self.__soap_ns = 'soapenv'  # 1.2
        else:
            self.__soap_ns = soap_ns

        # SOAP Server (special cases like oracle, jbossas6 or jetty)
        self.__soap_server = soap_server

        # SOAP Header support
        self.__headers = {}         # general headers
        self.__call_headers = None  # OrderedDict to be marshalled for RPC Call

        # check if the Certification Authority Cert is a string and store it
        if cacert and cacert.startswith("-----BEGIN CERTIFICATE-----"):
            fd, filename = tempfile.mkstemp()
            f = os.fdopen(fd, 'w+b', -1)
            log.debug("Saving CA certificate to %s" % filename)
            f.write(cacert)
            cacert = filename
            f.close()
        self.cacert = cacert

        if timeout is _USE_GLOBAL_DEFAULT:
            timeout = TIMEOUT
        else:
            timeout = timeout

        # Create HTTP wrapper
        Http = get_Http()
        self.http = Http(timeout=timeout, cacert=cacert, proxy=proxy, sessions=sessions)

        self.__ns = ns  # namespace prefix or False to not use it
        if not ns:
            self.__xml = """<?xml version="1.0" encoding="UTF-8"?>
<%(soap_ns)s:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:%(soap_ns)s="%(soap_uri)s">
<%(soap_ns)s:Header/>
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

        # parse wsdl url
        self.services = wsdl and self.wsdl_parse(wsdl, cache=cache)
        self.service_port = None                 # service port for late binding

    def __getattr__(self, attr):
        """Return a pseudo-method that can be called"""
        if not self.services:  # not using WSDL?
            return lambda self=self, *args, **kwargs: self.call(attr, *args, **kwargs)
        else:  # using WSDL:
            return lambda *args, **kwargs: self.wsdl_call(attr, *args, **kwargs)

    def call(self, method, *args, **kwargs):
        """Prepare xml request and make SOAP call, returning a SimpleXMLElement.

        If a keyword argument called "headers" is passed with a value of a
        SimpleXMLElement object, then these headers will be inserted into the
        request.
        """
        #TODO: method != input_message
        # Basic SOAP request:
        xml = self.__xml % dict(method=method, namespace=self.namespace, ns=self.__ns,
                                soap_ns=self.__soap_ns, soap_uri=soap_namespaces[self.__soap_ns])
        request = SimpleXMLElement(xml, namespace=self.__ns and self.namespace, prefix=self.__ns)

        try:
            request_headers = kwargs.pop('headers')
        except KeyError:
            request_headers = None

        # serialize parameters
        if kwargs:
            parameters = kwargs.items()
        else:
            parameters = args
        if parameters and isinstance(parameters[0], SimpleXMLElement):
            # merge xmlelement parameter ("raw" - already marshalled)
            if parameters[0].children() is not None:
                for param in parameters[0].children():
                    getattr(request, method).import_node(param)
        elif parameters:
            # marshall parameters:
            for k, v in parameters:  # dict: tag=valor
                getattr(request, method).marshall(k, v)
        elif not self.__soap_server in ('oracle', ) or self.__soap_server in ('jbossas6',):
            # JBossAS-6 requires no empty method parameters!
            delattr(request("Body", ns=soap_namespaces.values(),), method)

        # construct header and parameters (if not wsdl given) except wsse
        if self.__headers and not self.services:
            self.__call_headers = dict([(k, v) for k, v in self.__headers.items()
                                        if not k.startswith("wsse:")])
        # always extract WS Security header and send it
        if 'wsse:Security' in self.__headers:
            #TODO: namespaces too hardwired, clean-up...
            header = request('Header', ns=soap_namespaces.values(),)
            k = 'wsse:Security'
            v = self.__headers[k]
            header.marshall(k, v, ns=False, add_children_ns=False)
            header(k)['xmlns:wsse'] = 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd'
            #<wsse:UsernameToken xmlns:wsu='http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd'>
        if self.__call_headers:
            header = request('Header', ns=soap_namespaces.values(),)
            for k, v in self.__call_headers.items():
                ##if not self.__ns:
                ##    header['xmlns']
                if isinstance(v, SimpleXMLElement):
                    # allows a SimpleXMLElement to be constructed and inserted
                    # rather than a dictionary. marshall doesn't allow ns: prefixes
                    # in dict key names
                    header.import_node(v)
                else:
                    header.marshall(k, v, ns=self.__ns, add_children_ns=False)
        if request_headers:
            header = request('Header', ns=soap_namespaces.values(),)
            for subheader in request_headers.children():
                header.import_node(subheader)

        self.xml_request = request.as_xml()
        self.xml_response = self.send(method, self.xml_request)
        response = SimpleXMLElement(self.xml_response, namespace=self.namespace,
                                    jetty=self.__soap_server in ('jetty', ))
        if self.exceptions and response("Fault", ns=soap_namespaces.values(), error=False):
            raise SoapFault(unicode(response.faultcode), unicode(response.faultstring))
        return response

    def send(self, method, xml):
        """Send SOAP request using HTTP"""
        if self.location == 'test': return
        # location = "%s" % self.location #?op=%s" % (self.location, method)
        location = str(self.location)

        if self.services:
            soap_action = str(self.action)
        else:
            soap_action = str(self.action) + method

        headers = {
            'Content-type': 'text/xml; charset="UTF-8"',
            'Content-length': str(len(xml)),
            "SOAPAction": "\"%s\"" % (soap_action)
        }
        headers.update(self.http_headers)
        log.info("POST %s" % location)
        log.debug('\n'.join(["%s: %s" % (k, v) for k, v in headers.items()]))
        log.debug(xml.decode("utf8", "ignore"))

        response, content = self.http.request(
            location, "POST", body=xml, headers=headers)
        self.response = response
        self.content = content

        log.debug('\n'.join(["%s: %s" % (k, v) for k, v in response.items()]))
        log.debug(content.decode("utf8", "ignore"))
        return content

    def get_operation(self, method):
        # try to find operation in wsdl file
        soap_ver = self.__soap_ns == 'soap12' and 'soap12' or 'soap11'
        if not self.service_port:
            for service_name, service in self.services.items():
                for port_name, port in [port for port in service['ports'].items()]:
                    if port['soap_ver'] == soap_ver:
                        self.service_port = service_name, port_name
                        break
                else:
                    raise RuntimeError("Cannot determine service in WSDL: "
                                       "SOAP version: %s" % soap_ver)
        else:
            port = self.services[self.service_port[0]]['ports'][self.service_port[1]]
        self.location = port['location']
        operation = port['operations'].get(unicode(method))
        if not operation:
            raise RuntimeError("Operation %s not found in WSDL: "
                               "Service/Port Type: %s" %
                               (method, self.service_port))
        return operation

    def wsdl_call(self, method, *args, **kwargs):
        "Pre and post process SOAP call, input and output parameters using WSDL"
        soap_uri = soap_namespaces[self.__soap_ns]
        operation = self.get_operation(method)

        # get i/o type declarations:
        input = operation['input']
        output = operation['output']
        header = operation.get('header')
        if 'action' in operation:
            self.action = operation['action']

        # construct header and parameters
        if header:
            self.__call_headers = sort_dict(header, self.__headers)
        if input and args:
            # convert positional parameters to named parameters:
            d = [(k, arg) for k, arg in zip(input.values()[0].keys(), args)]
            kwargs.update(dict(d))
        if input and kwargs:
            params = sort_dict(input.values()[0], kwargs).items()
            if self.__soap_server == "axis":
                # use the operation name
                method = method
            else:
                # use the message (element) name
                method = input.keys()[0]
        #elif not input:
            #TODO: no message! (see wsmtxca.dummy)
        else:
            params = kwargs and kwargs.items()
        # call remote procedure
        response = self.call(method, *params)
        # parse results:
        resp = response('Body', ns=soap_uri).children().unmarshall(output)
        return resp and resp.values()[0]  # pass Response tag children

    def help(self, method):
        """Return operation documentation and invocation/returned value example"""
        operation = self.get_operation(method)
        input = operation.get('input')
        input = input and input.values() and input.values()[0]
        if isinstance(input, dict):
            input = ", ".join("%s=%s" % (k, repr(v)) for k, v in input.items())
        elif isinstance(input, list):
            input = repr(input)
        output = operation.get('output')
        if output:
            output = operation['output'].values()[0]
        headers = operation.get('headers') or None
        return "%s(%s)\n -> %s:\n\n%s\nHeaders: %s" % (
            method,
            input or "",
            output and output or "",
            operation.get("documentation", ""),
            headers,
        )

    def wsdl_parse(self, url, cache=False):
        """Parse Web Service Description v1.1"""

        log.debug("wsdl url: %s" % url)
        # Try to load a previously parsed wsdl:
        force_download = False
        if cache:
            # make md5 hash of the url for caching...
            filename_pkl = "%s.pkl" % hashlib.md5(url).hexdigest()
            if isinstance(cache, basestring):
                filename_pkl = os.path.join(cache, filename_pkl)
            if os.path.exists(filename_pkl):
                log.debug("Unpickle file %s" % (filename_pkl, ))
                f = open(filename_pkl, "r")
                pkl = pickle.load(f)
                f.close()
                # sanity check:
                if pkl['version'][:-1] != __version__.split(" ")[0][:-1] or pkl['url'] != url:
                    import warnings
                    warnings.warn('version or url mismatch! discarding cached wsdl', RuntimeWarning)
                    log.debug('Version: %s %s' % (pkl['version'], __version__))
                    log.debug('URL: %s %s' % (pkl['url'], url))
                    force_download = True
                else:
                    self.namespace = pkl['namespace']
                    self.documentation = pkl['documentation']
                    return pkl['services']

        soap_ns = {
            "http://schemas.xmlsoap.org/wsdl/soap/": 'soap11',
            "http://schemas.xmlsoap.org/wsdl/soap12/": 'soap12',
        }
        wsdl_uri = "http://schemas.xmlsoap.org/wsdl/"
        xsd_uri = "http://www.w3.org/2001/XMLSchema"
        xsi_uri = "http://www.w3.org/2001/XMLSchema-instance"

        get_local_name = lambda s: s and str((':' in s) and s.split(':')[1] or s)
        get_namespace_prefix = lambda s: s and str((':' in s) and s.split(':')[0] or None)

        # always return an unicode object:
        REVERSE_TYPE_MAP['string'] = unicode

        # Open uri and read xml:
        xml = fetch(url, self.http, cache, force_download, self.wsdl_basedir)
        # Parse WSDL XML:
        wsdl = SimpleXMLElement(xml, namespace=wsdl_uri)

        # detect soap prefix and uri (xmlns attributes of <definitions>)
        xsd_ns = None
        soap_uris = {}
        for k, v in wsdl[:]:
            if v in soap_ns and k.startswith("xmlns:"):
                soap_uris[get_local_name(k)] = v
            if v == xsd_uri and k.startswith("xmlns:"):
                xsd_ns = get_local_name(k)

        # Extract useful data:
        self.namespace = wsdl['targetNamespace']
        self.documentation = unicode(wsdl('documentation', error=False) or '')

        services = {}
        bindings = {}            # binding_name: binding
        operations = {}          # operation_name: operation
        port_type_bindings = {}  # port_type_name: binding
        messages = {}            # message: element
        elements = {}            # element: type def

        for service in wsdl.service:
            service_name = service['name']
            if not service_name:
                continue  # empty service?
            log.debug("Processing service %s" % service_name)
            serv = services.setdefault(service_name, {'ports': {}})
            serv['documentation'] = service['documentation'] or ''
            for port in service.port:
                binding_name = get_local_name(port['binding'])
                operations[binding_name] = {}
                address = port('address', ns=soap_uris.values(), error=False)
                location = address and address['location'] or None
                soap_uri = address and soap_uris.get(address.get_prefix())
                soap_ver = soap_uri and soap_ns.get(soap_uri)
                bindings[binding_name] = {'name': binding_name,
                                          'service_name': service_name,
                                          'location': location,
                                          'soap_uri': soap_uri,
                                          'soap_ver': soap_ver, }
                serv['ports'][port['name']] = bindings[binding_name]

        for binding in wsdl.binding:
            binding_name = binding['name']
            soap_binding = binding('binding', ns=soap_uris.values(), error=False)
            transport = soap_binding and soap_binding['transport'] or None
            port_type_name = get_local_name(binding['type'])
            bindings[binding_name].update({
                'port_type_name': port_type_name,
                'transport': transport, 'operations': {},
            })
            if port_type_name not in port_type_bindings:
                port_type_bindings[port_type_name] = []
            port_type_bindings[port_type_name].append(bindings[binding_name])
            for operation in binding.operation:
                op_name = operation['name']
                op = operation('operation', ns=soap_uris.values(), error=False)
                action = op and op['soapAction']
                d = operations[binding_name].setdefault(op_name, {})
                bindings[binding_name]['operations'][op_name] = d
                d.update({'name': op_name})
                d['parts'] = {}
                # input and/or ouput can be not present!
                input = operation('input', error=False)
                body = input and input('body', ns=soap_uris.values(), error=False)
                d['parts']['input_body'] = body and body['parts'] or None
                output = operation('output', error=False)
                body = output and output('body', ns=soap_uris.values(), error=False)
                d['parts']['output_body'] = body and body['parts'] or None
                header = input and input('header', ns=soap_uris.values(), error=False)
                d['parts']['input_header'] = header and {'message': header['message'], 'part': header['part']} or None
                header = output and output('header', ns=soap_uris.values(), error=False)
                d['parts']['output_header'] = header and {'message': header['message'], 'part': header['part']} or None
                if action:
                    d["action"] = action

        # check axis2 namespace at schema types attributes
        self.namespace = dict(wsdl.types("schema", ns=xsd_uri)[:]).get('targetNamespace', self.namespace)

        imported_schemas = {}

        # process current wsdl schema:
        for schema in wsdl.types("schema", ns=xsd_uri):
            preprocess_schema(schema, imported_schemas, elements, xsd_uri, self.__soap_server, self.http, cache, force_download, self.wsdl_basedir)

        postprocess_element(elements)

        for message in wsdl.message:
            log.debug("Processing message %s" % message['name'])
            for part in message('part', error=False) or []:
                element = {}
                element_name = part['element']
                if not element_name:
                    # some implementations (axis) uses type instead
                    element_name = part['type']
                type_ns = get_namespace_prefix(element_name)
                type_uri = wsdl.get_namespace_uri(type_ns)
                if type_uri == xsd_uri:
                    element_name = get_local_name(element_name)
                    fn = REVERSE_TYPE_MAP.get(unicode(element_name), None)
                    element = {part['name']: fn}
                    # emulate a true Element (complexType)
                    messages.setdefault((message['name'], None), {message['name']: OrderedDict()}).values()[0].update(element)
                else:
                    element_name = get_local_name(element_name)
                    fn = elements.get(make_key(element_name, 'element'))
                    if not fn:
                        # some axis servers uses complexType for part messages
                        fn = elements.get(make_key(element_name, 'complexType'))
                        element = {message['name']: {part['name']: fn}}
                    else:
                        element = {element_name: fn}
                    messages[(message['name'], part['name'])] = element

        for port_type in wsdl.portType:
            port_type_name = port_type['name']
            log.debug("Processing port type %s" % port_type_name)

            for binding in port_type_bindings[port_type_name]:
                for operation in port_type.operation:
                    op_name = operation['name']
                    op = operations[str(binding['name'])][op_name]
                    op['documentation'] = unicode(operation('documentation', error=False) or '')
                    if binding['soap_ver']:
                        #TODO: separe operation_binding from operation (non SOAP?)
                        if operation("input", error=False):
                            input_msg = get_local_name(operation.input['message'])
                            input_header = op['parts'].get('input_header')
                            if input_header:
                                header_msg = get_local_name(input_header.get('message'))
                                header_part = get_local_name(input_header.get('part'))
                                # warning: some implementations use a separate message!
                                header = get_message(messages, header_msg or input_msg, header_part)
                            else:
                                header = None   # not enought info to search the header message:
                            op['input'] = get_message(messages, input_msg, op['parts'].get('input_body'))
                            op['header'] = header
                        else:
                            op['input'] = None
                            op['header'] = None
                        if operation("output", error=False):
                            output_msg = get_local_name(operation.output['message'])
                            op['output'] = get_message(messages, output_msg, op['parts'].get('output_body'))
                        else:
                            op['output'] = None

        # dump the full service/port/operation map
        #log.debug(pprint.pformat(services))

        # Save parsed wsdl (cache)
        if cache:
            f = open(filename_pkl, "wb")
            pkl = {
                'version': __version__.split(" ")[0],
                'url': url,
                'namespace': self.namespace,
                'documentation': self.documentation,
                'services': services,
            }
            pickle.dump(pkl, f)
            f.close()

        return services

    def __setitem__(self, item, value):
        """Set SOAP Header value - this header will be sent for every request."""
        self.__headers[item] = value

    def close(self):
        """Finish the connection and remove temp files"""
        self.http.close()
        if self.cacert.startswith(tempfile.gettempdir()):
            log.debug("removing %s" % self.cacert)
            os.unlink(self.cacert)


def parse_proxy(proxy_str):
    """Parses proxy address user:pass@host:port into a dict suitable for httplib2"""
    if isinstance(proxy_str, unicode):
        proxy_str = proxy_str.encode("utf8")
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


if __name__ == "__main__":
    pass
