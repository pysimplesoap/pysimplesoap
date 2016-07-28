''' wsdl parsing module '''
import os
import copy
import logging
logger = logging.getLogger(__name__)
from .helpers import REVERSE_TYPE_MAP, fetch, urlsplit, get_local_name, preprocess_schema, \
        postprocess_element, get_namespace_prefix, Struct, make_key, get_message
from .transport import get_Http
from .simplexml import SimpleXMLElement

__all__ = ('parse', )


soap_ns_uris = {
    'http://schemas.xmlsoap.org/wsdl/soap/': 'soap11',
    'http://schemas.xmlsoap.org/wsdl/soap12/': 'soap12',
}
wsdl_uri = 'http://schemas.xmlsoap.org/wsdl/'
xsd_uri = 'http://www.w3.org/2001/XMLSchema'
xsi_uri = 'http://www.w3.org/2001/XMLSchema-instance'

def parse(wsdl_path):
    logger.debug('Parsing wsdl path: %s' % wsdl_path)
    # always return an unicode object:
    REVERSE_TYPE_MAP['string'] = str

    # TODO: extract "fetch_wsdl" function
    # Open uri and read xml:
    Http = get_Http()
    http = Http(timeout=60, cacert=None, proxy=None, sessions=False)
    _, netloc, path, _, _ = urlsplit(wsdl_path)
    wsdl_basedir = os.path.dirname(netloc + path)
    xml = fetch(wsdl_path, http, False, False, wsdl_basedir, {})
    # Parse WSDL XML:
    wsdl = SimpleXMLElement(xml, namespace=wsdl_uri)

    # some wsdl are split down in several files, join them:
    wsdl = _merge_imported_wsdl(wsdl, http, wsdl_basedir)

    # detect soap prefix and uri (xmlns attributes of <definitions>)
    soap_uris = {}
    for k, v in wsdl[:]:
        if v in soap_ns_uris and k.startswith('xmlns:'):
            soap_uris[get_local_name(k)] = v

    # check axis2 namespace at schema types attributes (europa.eu checkVat)
    elements = _parse_imported_schemas(wsdl, http, wsdl_basedir)
    messages = _parse_message(wsdl, elements)
    port_types = _parse_port_types(wsdl)
    bindings = _parse_bindings(wsdl, port_types, soap_uris, messages)
    services = _parse_services(wsdl, bindings, soap_uris)

    # create an default service if none is given in the wsdl:
    if not services:
        services[''] = {'ports': {'': None}}

    return services


def _merge_imported_wsdl(wsdl, http, wsdl_basedir):
    imported_wsdls = {}
    for element in wsdl.children() or []:
        if element.get_local_name() in ('import'):
            wsdl_namespace = element['namespace']
            wsdl_location = element['location']
            if wsdl_location is None:
                logger.warning('WSDL location not provided for %s!' % wsdl_namespace)
                continue
            if wsdl_location in imported_wsdls:
                logger.warning('WSDL %s already imported!' % wsdl_location)
                continue
            imported_wsdls[wsdl_location] = wsdl_namespace
            logger.debug('Importing wsdl %s from %s' % (wsdl_namespace, wsdl_location))
            # Open uri and read xml:
            xml = fetch(wsdl_location, http, False, False, wsdl_basedir, {})
            # Parse imported XML schema (recursively):
            imported_wsdl = SimpleXMLElement(xml, namespace=xsd_uri)
            # merge the imported wsdl into the main document:
            wsdl.import_node(imported_wsdl)
            # warning: do not process schemas to avoid infinite recursion!

    return wsdl


def _parse_imported_schemas(wsdl, http, wsdl_basedir):
    elements = {}
    imported_schemas = {}
    global_namespaces = _get_global_namespaces(wsdl)

    for types in wsdl('types', error=False) or []:
        # avoid issue if schema is not given in the main WSDL file
        schemas = types('schema', ns=xsd_uri, error=False)
        for schema in schemas or []:
            preprocess_schema(schema, imported_schemas, elements, xsd_uri,
                              None, http, False,
                              False, wsdl_basedir,
                              global_namespaces=global_namespaces)

    postprocess_element(elements, [])

    return elements


def _get_global_namespaces(wsdl):
    namespace = ''
    if "http://xml.apache.org/xml-soap" in dict(wsdl[:]).values():
        # get the sub-namespace in the first schema element (see issue 8)
        if wsdl('types', error=False):
            schema = wsdl.types('schema', ns=xsd_uri)
            attrs = dict(schema[:])
            namespace = attrs.get('targetNamespace', namespace)
        if not namespace or namespace == "urn:DefaultNamespace":
            namespace = wsdl['targetNamespace'] or namespace


    return {None: namespace}


def _parse_message(wsdl, elements):
    messages = {}
    for message in wsdl.message:
        for part in message('part', error=False) or []:
            element = {}
            element_name = part['element']
            if not element_name:
                # some implementations (axis) uses type instead
                element_name = part['type']
            type_ns = get_namespace_prefix(element_name)
            type_uri = part.get_namespace_uri(type_ns)
            part_name = part['name'] or None
            if type_uri == xsd_uri:
                element_name = get_local_name(element_name)
                fn = REVERSE_TYPE_MAP.get(element_name, None)
                element = {part_name: fn}
                # emulate a true Element (complexType) for rpc style
                if (message['name'], part_name) not in messages:
                    od = Struct()
                    od.namespaces[None] = type_uri
                    messages[(message['name'], part_name)] = {message['name']: od}
                else:
                    od = messages[(message['name'], part_name)].values()[0]
                od.namespaces[part_name] = type_uri
                od.references[part_name] = False
                od.update(element)
            else:
                element_name = get_local_name(element_name)
                fn = elements.get(make_key(element_name, 'element', type_uri))
                if not fn:
                    # some axis servers uses complexType for part messages (rpc)
                    fn = elements.get(make_key(element_name, 'complexType', type_uri))
                    od = Struct()
                    od[part_name] = fn
                    od.namespaces[None] = type_uri
                    od.namespaces[part_name] = type_uri
                    od.references[part_name] = False
                    element = {message['name']: od}
                else:
                    element = {element_name: fn}
                messages[(message['name'], part_name)] = element

    return messages


def _parse_port_types(wsdl):
    port_types = {}

    for port_type_node in wsdl.portType:
        port_type_name = port_type_node['name']
        port_type = port_types[port_type_name] = {}
        operations = port_type['operations'] = {}

        for operation_node in port_type_node.operation:
            op_name = operation_node['name']
            op = operations[op_name] = {}
            op['style'] = operation_node['style']
            op['parameter_order'] = (operation_node['parameterOrder'] or "").split(" ")
            op['documentation'] = unicode(operation_node('documentation', error=False)) or ''

            if operation_node('input', error=False):
                op['input_msg'] = get_local_name(operation_node.input['message'])
                ns = get_namespace_prefix(operation_node.input['message'])
                op['namespace'] = operation_node.get_namespace_uri(ns)

            if operation_node('output', error=False):
                op['output_msg'] = get_local_name(operation_node.output['message'])

            #Get all fault message types this operation may return
            fault_msgs = op['fault_msgs'] = {}
            faults = operation_node('fault', error=False)
            if faults is not None:
                for fault in operation_node('fault', error=False):
                    fault_msgs[fault['name']] = get_local_name(fault['message'])

    return port_types


def _parse_bindings(wsdl, port_types, soap_uris, messages):
    bindings = {}

    for binding_node in wsdl.binding:
        port_type_name = get_local_name(binding_node['type'])
        if port_type_name not in port_types:
            # Invalid port type
            continue
        port_type = port_types[port_type_name]
        binding_name = binding_node['name']
        soap_binding = binding_node('binding', ns=list(soap_uris.values()), error=False)
        transport = soap_binding and soap_binding['transport'] or None
        style = soap_binding and soap_binding['style'] or None  # rpc

        binding = bindings[binding_name] = {
            'name': binding_name,
            'operations': copy.deepcopy(port_type['operations']),
            'port_type_name': port_type_name,
            'transport': transport,
            'style': style,
        }

        for operation_node in binding_node.operation:
            op_name = operation_node['name']
            op_op = operation_node('operation', ns=list(soap_uris.values()), error=False)
            action = op_op and op_op['soapAction']

            op = binding['operations'].setdefault(op_name, {})
            op['name'] = op_name
            op['style'] = op.get('style', style)
            if action is not None:
                op['action'] = action

            # input and/or output can be not present!
            input = operation_node('input', error=False)
            body = input and input('body', ns=list(soap_uris.values()), error=False)
            parts_input_body = body and body['parts'] or None

            # parse optional header messages (some implementations use more than one!)
            parts_input_headers = []
            headers = input and input('header', ns=list(soap_uris.values()), error=False)
            for header in headers or []:
                hdr = {'message': header['message'], 'part': header['part']}
                parts_input_headers.append(hdr)

            if 'input_msg' in op:
                headers = {}    # base header message structure
                for input_header in parts_input_headers:
                    header_msg = get_local_name(input_header.get('message'))
                    header_part = get_local_name(input_header.get('part'))
                    # warning: some implementations use a separate message!
                    hdr = get_message(messages, header_msg or op['input_msg'], header_part)
                    if hdr:
                        headers.update(hdr)
                    else:
                        pass # not enough info to search the header message:
                op['input'] = get_message(messages, op['input_msg'], parts_input_body, op['parameter_order'])
                op['header'] = headers

                try:
                    element = list(op['input'].values())[0]
                    ns_uri = element.namespaces[None]
                    qualified = element.qualified
                except (AttributeError, KeyError):
                    # TODO: fix if no parameters parsed or "variants"
                    ns_uri = op['namespace']
                    qualified = None
                if ns_uri:
                    op['namespace'] = ns_uri
                    op['qualified'] = qualified

                # Remove temporary property
                del op['input_msg']

            else:
                op['input'] = None
                op['header'] = None

            output = operation_node('output', error=False)
            body = output and output('body', ns=list(soap_uris.values()), error=False)
            parts_output_body = body and body['parts'] or None
            if 'output_msg' in op:
                op['output'] = get_message(messages, op['output_msg'], parts_output_body)
                # Remove temporary property
                del op['output_msg']
            else:
                op['output'] = None

            if 'fault_msgs' in op:
                faults = op['faults'] = {}
                for msg in op['fault_msgs'].values():
                    msg_obj = get_message(messages, msg, parts_output_body)
                    tag_name = list(msg_obj)[0]
                    faults[tag_name] = msg_obj

            # useless? never used
            parts_output_headers = []
            headers = output and output('header', ns=list(soap_uris.values()), error=False)
            for header in headers or []:
                hdr = {'message': header['message'], 'part': header['part']}
                parts_output_headers.append(hdr)

    return bindings


def _parse_services(wsdl, bindings, soap_uris):
    services = {}

    for service in wsdl("service", error=False) or []:
        service_name = service['name']
        if not service_name:
            continue  # empty service?

        serv = services.setdefault(service_name, {})
        ports = serv['ports'] = {}
        serv['documentation'] = service['documentation'] or ''
        for port in service.port:
            binding_name = get_local_name(port['binding'])

            if not binding_name in bindings:
                continue    # unknown binding

            binding = ports[port['name']] = copy.deepcopy(bindings[binding_name])
            address = port('address', ns=list(soap_uris.values()), error=False)
            location = address and address['location'] or None
            soap_uri = address and soap_uris.get(address.get_prefix())
            soap_ver = soap_uri and soap_ns_uris.get(soap_uri)

            binding.update({
                'location': location,
                'service_name': service_name,
                'soap_uri': soap_uri,
                'soap_ver': soap_ver,
            })

    return services
