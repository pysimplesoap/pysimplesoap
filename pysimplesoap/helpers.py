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

"""Pythonic simple SOAP Client helpers"""


from __future__ import unicode_literals
import sys
if sys.version > '3':
    basestring = str

import os
import logging
import hashlib
try:
    import urllib2
    from urlparse import urlsplit
except ImportError:
    from urllib import request as urllib2
    from urllib.parse import urlsplit

from . import __author__, __copyright__, __license__, __version__
from .simplexml import SimpleXMLElement, TYPE_MAP, REVERSE_TYPE_MAP, OrderedDict

log = logging.getLogger(__name__)


def fetch(url, http, cache=False, force_download=False, wsdl_basedir=''):
    """Download a document from a URL, save it locally if cache enabled"""

    # check / append a valid schema if not given:
    url_scheme, netloc, path, query, fragment = urlsplit(url)
    if not url_scheme in ('http', 'https', 'file'):
        for scheme in ('http', 'https', 'file'):
            try:
                if not url.startswith("/") and scheme in ('http', 'https'):
                    tmp_url = "%s://%s" % (scheme, os.path.join(wsdl_basedir, url))
                else:
                    tmp_url = "%s:%s" % (scheme, os.path.join(wsdl_basedir, url))
                log.debug('Scheme not found, trying %s' % scheme)
                return fetch(tmp_url, http, cache, force_download, wsdl_basedir)
            except Exception as e:
                log.error(e)
        raise RuntimeError('No scheme given for url: %s' % url)

    # make md5 hash of the url for caching...
    filename = '%s.xml' % hashlib.md5(url.encode('utf8')).hexdigest()
    if isinstance(cache, basestring):
        filename = os.path.join(cache, filename)
    if cache and os.path.exists(filename) and not force_download:
        log.info('Reading file %s' % filename)
        f = open(filename, 'r')
        xml = f.read()
        f.close()
    else:
        if url_scheme == 'file':
            log.info('Fetching url %s using urllib2' % url)
            f = urllib2.urlopen(url)
            xml = f.read()
        else:
            log.info('GET %s using %s' % (url, http._wrapper_version))
            response, xml = http.request(url, 'GET', None, {})
        if cache:
            log.info('Writing file %s' % filename)
            if not os.path.isdir(cache):
                os.makedirs(cache)
            f = open(filename, 'w')
            f.write(xml)
            f.close()
    return xml


def sort_dict(od, d):
    """Sort parameters (same order as xsd:sequence)"""
    if isinstance(od, dict):
        ret = OrderedDict()
        for k in od.keys():
            v = d.get(k)
            # don't append null tags!
            if v is not None:
                if isinstance(v, dict):
                    v = sort_dict(od[k], v)
                elif isinstance(v, list):
                    v = [sort_dict(od[k][0], v1) for v1 in v]
                ret[k] = v
        return ret
    else:
        return d


def make_key(element_name, element_type):
    """Return a suitable key for elements"""
    # only distinguish 'element' vs other types
    if element_type in ('complexType', 'simpleType'):
        eltype = 'complexType'
    else:
        eltype = element_type
    if eltype not in ('element', 'complexType', 'simpleType'):
        raise RuntimeError("Unknown element type %s = %s" % (element_name, eltype))
    return (element_name, eltype)


def process_element(elements, element_name, node, element_type, xsd_uri, dialect):
    """Parse and define simple element types"""

    log.debug('Processing element %s %s' % (element_name, element_type))
    for tag in node:
        if tag.get_local_name() in ('annotation', 'documentation'):
            continue
        elif tag.get_local_name() in ('element', 'restriction'):
            log.debug('%s has no children! %s' % (element_name, tag))
            children = tag  # element "alias"?
            alias = True
        elif tag.children():
            children = tag.children()
            alias = False
        else:
            log.debug('%s has no children! %s' % (element_name, tag))
            continue  # TODO: abstract?
        d = OrderedDict()
        for e in children:
            t = e['type']
            if not t:
                t = e['base']  # complexContent (extension)!
            if not t:
                t = 'anyType'  # no type given!
            t = t.split(":")
            if len(t) > 1:
                ns, type_name = t
            else:
                ns, type_name = None, t[0]
            if element_name == type_name:
                pass  # warning with infinite recursion
            uri = ns and e.get_namespace_uri(ns) or xsd_uri
            if uri == xsd_uri:
                # look for the type, None == any
                fn = REVERSE_TYPE_MAP.get(type_name, None)
            else:
                fn = None
            if not fn:
                # simple / complex type, postprocess later
                fn = elements.setdefault(make_key(type_name, 'complexType'), OrderedDict())

            if e['maxOccurs'] == 'unbounded' or (ns == 'SOAP-ENC' and type_name == 'Array'):
                # it's an array... TODO: compound arrays?
                if isinstance(fn, OrderedDict):
                    if len(children) > 1 and dialect in ('jetty',):
                        # Jetty style support
                        # {'ClassName': [{'attr1': val1, 'attr2': val2}]
                        fn.array = True
                    else:
                        # .NET style support (backward compatibility)
                        # [{'ClassName': {'attr1': val1, 'attr2': val2}]
                        d.array = True
                else:
                    if dialect in ('jetty',):
                        # scalar support [{'attr1': [val1]}]
                        fn = [fn]
                    else:
                        d.array = True

            if e['name'] is not None and not alias:
                e_name = e['name']
                d[e_name] = fn
            else:
                log.debug('complexContent/simpleType/element %s = %s' % (element_name, type_name))
                d[None] = fn
            if e is not None and e.get_local_name() == 'extension' and e.children():
                # extend base element:
                process_element(elements, element_name, e.children(), element_type, xsd_uri, dialect)
        elements.setdefault(make_key(element_name, element_type), OrderedDict()).update(d)


def postprocess_element(elements):
    """Fix unresolved references (elements referenced before its definition, thanks .net)"""
    for k, v in elements.items():
        if isinstance(v, OrderedDict):
            if v != elements:  # TODO: fix recursive elements
                postprocess_element(v)
            if None in v and v[None]:  # extension base?
                if isinstance(v[None], dict):
                    for i, kk in enumerate(v[None]):
                        # extend base -keep orginal order-
                        if v[None] is not None:
                            elements[k].insert(kk, v[None][kk], i)
                    del v[None]
                else:  # "alias", just replace
                    log.debug('Replacing %s = %s' % (k, v[None]))
                    elements[k] = v[None]
                    #break
            if v.array:
                elements[k] = [v]  # convert arrays to python lists
        if isinstance(v, list):
            for n in v:  # recurse list
                if isinstance(n, (OrderedDict, list)):
                    postprocess_element(n)


def get_message(messages, message_name, part_name):
    if part_name:
        # get the specific part of the message:
        return messages.get((message_name, part_name))
    else:
        # get the first part for the specified message:
        for (message_name_key, part_name_key), message in messages.items():
            if message_name_key == message_name:
                return message


def preprocess_schema(schema, imported_schemas, elements, xsd_uri, dialect, http, cache, force_download, wsdl_basedir):
    """Find schema elements and complex types"""
    for element in schema.children() or []:
        if element.get_local_name() in ('import', 'include',):
            schema_namespace = element['namespace']
            schema_location = element['schemaLocation']
            if schema_location is None:
                log.debug('Schema location not provided for %s!' % schema_namespace)
                continue
            if schema_location in imported_schemas:
                log.debug('Schema %s already imported!' % schema_location)
                continue
            imported_schemas[schema_location] = schema_namespace
            log.debug('Importing schema %s from %s' % (schema_namespace, schema_location))
            # Open uri and read xml:
            xml = fetch(schema_location, http, cache, force_download, wsdl_basedir)

            # Parse imported XML schema (recursively):
            imported_schema = SimpleXMLElement(xml, namespace=xsd_uri)
            preprocess_schema(imported_schema, imported_schemas, elements, xsd_uri, dialect, http, cache, force_download, wsdl_basedir)

        element_type = element.get_local_name()
        if element_type in ('element', 'complexType', "simpleType"):
            element_name = element['name']
            log.debug("Parsing Element %s: %s" % (element_type, element_name))
            if element.get_local_name() == 'complexType':
                children = element.children()
            elif element.get_local_name() == 'simpleType':
                children = element('restriction', ns=xsd_uri)
            elif element.get_local_name() == 'element' and element['type']:
                children = element
            else:
                children = element.children()
                if children:
                    children = children.children()
                elif element.get_local_name() == 'element':
                    children = element
            if children:
                process_element(elements, element_name, children, element_type, xsd_uri, dialect)
