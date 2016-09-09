#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Pythonic simple SOAP Client implementation"""

from __future__ import unicode_literals
import sys
if sys.version > '3':
    unicode = str

import logging
import os
import tempfile
import requests

from .simplexml import SimpleXMLElement
# Utility functions used throughout wsdl_parse, moved aside for readability
from .helpers import Alias, sort_dict, TYPE_MAP, urlsplit, Struct
from .mime import MimeGenerator
from .env import SOAP_NAMESPACES
from .env import TIMEOUT
from .api import decode
from .wsdl import parse

log = logging.getLogger(__name__)


class SoapClient(object):
    """Simple SOAP Client (simil PHP)"""
    def __init__(self, location=None, action=None, namespace='',
                 cert=None, proxy=None, ns=None,
                 soap_ns=None, wsdl=None, wsdl_basedir='', cacert=None,
                 sessions=False, soap_server=None, timeout=TIMEOUT,
                 http_headers=None, username=None, password=None,
                 key_file=None, **kwds):
        """
        :param http_headers: Additional HTTP Headers; example: {'Host': 'ipsec.example.com'}
        """
        self.location = location        # server location (url)
        self.action = action            # SOAP base action
        self.namespace = namespace      # message
        self.http_headers = http_headers or {}
        # extract the base directory / url for wsdl relative imports:
        if wsdl and wsdl_basedir == '':
            # parse the wsdl url, strip the scheme and filename
            _, netloc, path, _, _ = urlsplit(wsdl)
            wsdl_basedir = os.path.dirname(netloc + path)

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
        self.__call_headers = None  # Struct to be marshalled for RPC Call

        # check if the Certification Authority Cert is a string and store it
        if cacert and cacert.startswith('-----BEGIN CERTIFICATE-----'):
            fd, filename = tempfile.mkstemp()
            log.debug("Saving CA certificate to %s" % filename)
            with os.fdopen(fd, 'w+b', -1) as f:
                f.write(cacert)
            cacert = filename
        self.cacert = cacert

        # Create HTTP wrapper
        self.http = requests.session()
        if username and password:
            self.http.auth = (username, password)
        if cert and key_file:
            self.http.cert = (key_file, cert)

        # namespace prefix, None to use xmlns attribute or False to not use it:
        self.__ns = ns
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
<%(soap_ns)s:Body><%(ns)s:%(method)s></%(ns)s:%(method)s></%(soap_ns)s:Body></%(soap_ns)s:Envelope>"""

        # parse wsdl url
        log.debug('wsdl: %s' % wsdl)
        self.services = wsdl and self.wsdl_parse(wsdl)
        self.service_port = None                 # service port for late binding

    def __getattr__(self, attr):
        """Return a pseudo-method that can be called"""
        if self.services: # using WSDL:
            return lambda *args, **kwargs: self.wsdl_call(attr, *args, **kwargs)
        else: # not using WSDL?
            return lambda *args, **kwargs: self.call(attr, *args, **kwargs)

    def call(self, method, attachments, *args, **kwargs):
        """Prepare xml request and make SOAP call, returning a SimpleXMLElement.

        If a keyword argument called "headers" is passed with a value of a
        SimpleXMLElement object, then these headers will be inserted into the
        request.
        """
        req_headers, request = self._generate_request(method, args, kwargs, attachments)

        resp_headers, resp_content = self.send(method, req_headers, request)

        return decode(resp_headers, resp_content, self.services, ns=self.__soap_ns, method=method)


    def _generate_request(self, method, args, kwargs, attachments):
        soap_uri = SOAP_NAMESPACES[self.__soap_ns]
        xml = self.__xml % dict(method=method,              # method tag name
                                namespace=self.namespace,   # method ns uri
                                ns=self.__ns,               # method ns prefix
                                soap_ns=self.__soap_ns,     # soap prefix & uri
                                soap_uri=soap_uri)
        request = SimpleXMLElement(xml, namespace=self.__ns and self.namespace,
                                        prefix=self.__ns)

        request_headers = kwargs.pop('headers', None)

        # serialize parameters
        if kwargs:
            parameters = list(kwargs.items())
        else:
            parameters = args
        if parameters and isinstance(parameters[0], SimpleXMLElement):
            body = request('Body', ns=SOAP_NAMESPACES.values())
            # remove default body parameter (method name)
            delattr(body, method)
            # merge xmlelement parameter ("raw" - already marshalled)
            body.import_node(parameters[0])
        elif parameters:
            # marshall parameters:
            use_ns = None if (self.__soap_server == "jetty" or self.qualified is False) else True
            sort_parameters = [para for element in self.get_operation(method)['input'][method] for para in parameters if element == para[0]]
            for k, v in sort_parameters:  # dict: tag=valor
                if hasattr(v, "namespaces") and use_ns:
                    ns = v.namespaces.get(None, True)
                else:
                    ns = use_ns
                getattr(request, method).marshall(k, v, ns=ns)
        elif self.__soap_server in ('jbossas6',):
            # JBossAS-6 requires no empty method parameters!
            delattr(request("Body", ns=SOAP_NAMESPACES.values()), method)

        # construct header and parameters (if not wsdl given) except wsse
        if self.__headers and not self.services:
            self.__call_headers = dict([(k, v) for k, v in self.__headers.items()
                                        if not k.startswith('wsse:')])

        if self.__call_headers:
            header = request('Header', ns=SOAP_NAMESPACES.values())
            for k, v in self.__call_headers.iteritems():
                if isinstance(v, SimpleXMLElement):
                    # allows a SimpleXMLElement to be constructed and inserted
                    # rather than a dictionary. marshall doesn't allow ns: prefixes
                    # in dict key names
                    header.import_node(v)
                else:
                    header.marshall(k, v, ns=self.__ns, add_children_ns=False)
        if request_headers:
            header = request('Header', ns=SOAP_NAMESPACES.values())
            for subheader in request_headers.children():
                header.import_node(subheader)

        if attachments:
            mime_gen = MimeGenerator(request.as_xml(), attachments)
            mime_gen.generate()
            return {'Content-type': 'multipart/related; type="text/xml"; boundary="%s"' % mime_gen.get_boundary()}, mime_gen.to_string()
        return {}, request.as_xml()

    def send(self, method, req_headers, xml):
        """Send SOAP request using HTTP"""
        if self.services:
            soap_action = str(self.action)
        else:
            soap_action = str(self.action) + method # TODO: what does this mean?
        headers = {
            'Content-type': 'text/xml; charset="UTF-8"',
            'Content-length': str(len(xml)),
        }
        headers.update(req_headers) # if req_headers set Content-type, it will be overrided

        if self.action:
            headers['SOAPAction'] = soap_action

        headers.update(self.http_headers)
        log.info("POST %s" % self.location)
        log.debug('\n'.join(["%s: %s" % (k, v) for k, v in headers.iteritems()]))
        log.debug(xml)

        if sys.version < '3':
            # Ensure http_method, location and all headers are binary to prevent
            # UnicodeError inside httplib.HTTPConnection._send_output.

            # httplib in python3 do the same inside itself, don't need to convert it here
            headers = dict((str(k), str(v)) for k, v in headers.iteritems())

        resp = self.http.post(self.location, data=xml, headers=headers)

        log.debug('\n'.join(["%s: %s" % (k, v) for k, v in resp.headers.iteritems()]))
        log.debug(resp.content)
        return (resp.headers, resp.content)

    def get_operation(self, method):
        # try to find operation in wsdl file
        soap_ver = self.__soap_ns.startswith('soap12') and 'soap12' or 'soap11'
        for service_name, service in self.services.iteritems():
            for port_name, port in service['ports'].iteritems():
                if port['soap_ver'] == soap_ver:
                    if method in port['operations']:
                        if not self.location:
                            self.location = port['location']
                        return port['operations'][method]

        raise RuntimeError('Cannot determine service in WSDL: '
                           'SOAP version: %s' % soap_ver)

    def wsdl_call(self, method, *args, **kwargs):
        """Pre and post process SOAP call, input and output parameters using WSDL"""
        return self.wsdl_call_with_args(method, args, kwargs)

    def wsdl_call_with_args(self, method, args, kwargs):
        """Pre and post process SOAP call, input and output parameters using WSDL"""
        operation = self.get_operation(method)

        # get i/o type declarations:
        input = operation['input']
        header = operation.get('header')
        if 'action' in operation:
            self.action = operation['action']

        if 'namespace' in operation:
            self.namespace = operation['namespace'] or ''
            self.qualified = operation['qualified']

        # construct header and parameters
        if header:
            self.__call_headers = sort_dict(header, self.__headers)
        attachments = [(k.split(':', 1)[1], v) for (k, v) in kwargs.iteritems() if k.startswith('cid:')]
        kwargs = dict((k,v) for k,v in kwargs.iteritems() if not k.startswith('cid:'))
        method, params = self.wsdl_call_get_params(method, input, args, kwargs)

        # call remote procedure
        return self.call(method, attachments, *params)

    def wsdl_call_get_params(self, method, input, args, kwargs):
        """Build params from input and args/kwargs"""
        params = inputname = inputargs = None
        all_args = {}
        if input:
            inputname = list(input.keys())[0]
            inputargs = input[inputname]

        if input and args:
            # convert positional parameters to named parameters:
            d = {}
            for idx, arg in enumerate(args):
                key = list(inputargs.keys())[idx]
                if isinstance(arg, dict):
                    if key not in arg:
                        raise KeyError('Unhandled key %s. use client.help(method)' % key)
                    d[key] = arg[key]
                else:
                    d[key] = arg
            all_args.update({inputname: d})

        if input and (kwargs or all_args):
            if kwargs:
                all_args.update({inputname: kwargs})
            valid, errors, warnings = self.wsdl_validate_params(input, all_args)
            if not valid:
                raise ValueError('Invalid Args Structure. Errors: %s' % errors)
            # sort and filter parameters according to wsdl input structure
            tree = sort_dict(input, all_args)
            root = list(tree.values())[0]
            params = []
            # make a params tuple list suitable for self.call(method, *params)
            for k, v in root.iteritems():
                # fix referenced namespaces as info is lost when calling call
                root_ns = root.namespaces[k]
                if not root.references[k] and isinstance(v, Struct):
                    v.namespaces[None] = root_ns
                params.append((k, v))
            # TODO: check style and document attributes
            if self.__soap_server in ('axis', ):
                # use the operation name
                method = method
            else:
                # use the message (element) name
                method = inputname
        else:
            params = kwargs and kwargs.iteritems()

        return (method, params)

    def wsdl_validate_params(self, struct, value):
        """Validate the arguments (actual values) for the parameters structure.
           Fail for any invalid arguments or type mismatches."""
        errors = []
        warnings = []
        valid = True

        # Determine parameter type
        if type(struct) == type(value):
            typematch = True
        if not isinstance(struct, dict) and isinstance(value, dict):
            typematch = True    # struct can be a dict or derived (Struct)
        else:
            typematch = False

        if struct == str:
            struct = unicode        # fix for py2 vs py3 string handling

        if not isinstance(struct, (list, dict, tuple)) and struct in TYPE_MAP:
            if not type(value) == struct  and value is not None:
                try:
                    struct(value)       # attempt to cast input to parameter type
                except:
                    valid = False
                    errors.append('Type mismatch for argument value. parameter(%s): %s, value(%s): %s' % (type(struct), struct, type(value), value))

        elif isinstance(struct, list) and len(struct) == 1 and not isinstance(value, list):
            # parameter can have a dict in a list: [{}] indicating a list is allowed, but not needed if only one argument.
            next_valid, next_errors, next_warnings = self.wsdl_validate_params(struct[0], value)
            if not next_valid:
                valid = False
            errors.extend(next_errors)
            warnings.extend(next_warnings)

        # traverse tree
        elif isinstance(struct, dict):
            if struct and value:
                for key in value:
                    if key not in struct:
                        valid = False
                        errors.append('Argument key %s not in parameter. parameter: %s, args: %s' % (key, struct, value))
                    else:
                        next_valid, next_errors, next_warnings = self.wsdl_validate_params(struct[key], value[key])
                        if not next_valid:
                            valid = False
                        errors.extend(next_errors)
                        warnings.extend(next_warnings)
                for key in struct:
                    if key not in value:
                        warnings.append('Parameter key %s not in args. parameter: %s, value: %s' % (key, struct, value))
            elif struct and not value:
                warnings.append('parameter keys not in args. parameter: %s, args: %s' % (struct, value))
            elif not struct and value:
                valid = False
                errors.append('Args keys not in parameter. parameter: %s, args: %s' % (struct, value))
            else:
                pass
        elif isinstance(struct, list):
            struct_list_value = struct[0]
            for item in value:
                next_valid, next_errors, next_warnings = self.wsdl_validate_params(struct_list_value, item)
                if not next_valid:
                    valid = False
                errors.extend(next_errors)
                warnings.extend(next_warnings)
        elif not typematch:
            valid = False
            errors.append('Type mismatch. parameter(%s): %s, value(%s): %s' % (type(struct), struct, type(value), value))

        return (valid, errors, warnings)

    def help(self, method):
        """Return operation documentation and invocation/returned value example"""
        operation = self.get_operation(method)
        input = operation.get('input')
        input = input and input.values() and list(input.values())[0]
        if isinstance(input, dict):
            input = ", ".join("%s=%s" % (k, repr(v)) for k, v in input.iteritems())
        elif isinstance(input, list):
            input = repr(input)
        output = operation.get('output')
        if output:
            output = list(operation['output'].values())[0]
        headers = operation.get('headers') or None
        return "%s(%s)\n -> %s:\n\n%s\nHeaders: %s" % (
            method,
            input or '',
            output and output or '',
            operation.get('documentation', ''),
            headers,
        )

    def wsdl_parse(self, url):
        _, _, _, _, services = parse(url)

        return services

    def __setitem__(self, item, value):
        """Set SOAP Header value - this header will be sent for every request."""
        self.__headers[item] = value

    def close(self):
        """Finish the connection and remove temp files"""
        self.http.close()
        if self.cacert.startswith(tempfile.gettempdir()):
            log.debug('removing %s' % self.cacert)
            os.unlink(self.cacert)

    def __repr__(self):
        s = 'SOAP CLIENT'
        s += '\n ELEMENTS'
        for e in self.elements:
            if isinstance(e, type):
                e = e.__name__
            elif isinstance(e, Alias):
                e = e.xml_type
            elif isinstance(e, Struct) and e.key[1]=='element':
                e = repr(e)
            else:
                continue
            s += '\n  %s' % e
        for service in self.services:
            s += '\n SERVICE (%s)' % service
            ports = self.services[service]['ports']
            for port in ports:
                port = ports[port]
                if port['soap_ver'] == None: continue
                s += '\n   PORT (%s)' % port['name']
                s += '\n    Location: %s' % port['location']
                s += '\n    Soap ver: %s' % port['soap_ver']
                s += '\n    Soap URI: %s' % port['soap_uri']
                s += '\n    OPERATIONS'
                operations = port['operations']
                for operation in sorted(operations):
                    operation = self.get_operation(operation)
                    input = operation.get('input')
                    input = input and input.values() and list(input.values())[0]
                    input_str = ''
                    if isinstance(input, dict):
                        if 'parameters' not in input or input['parameters']!=None:
                            for k, v in input.items():
                                if isinstance(v, type):
                                    v = v.__name__
                                elif isinstance(v, Alias):
                                    v = v.xml_type
                                elif isinstance(v, Struct):
                                    v = v.key[0]
                                input_str += '%s: %s, ' % (k, v)
                    output = operation.get('output')
                    if output:
                        output = list(operation['output'].values())[0]
                    s += '\n     %s(%s)' % (
                        operation['name'],
                        input_str[:-2]
                        )
                    s += '\n      > %s' % output

        return s

