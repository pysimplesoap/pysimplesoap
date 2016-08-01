''' API module for functional usage like encode/decode '''
from .wsdl import parse
from .simplexml import SimpleXMLElement


SOAPENV = 'http://schemas.xmlsoap.org/soap/envelope/'

def decode(headers, content, wsdl, soap_ver='soap11'):
    (elements, messages, port_types, bindings, services) = parse(wsdl)
    response = SimpleXMLElement(content, headers=headers)
    method = headers['soapaction'].rsplit('/', 1)[1]

    def get_operation():
        service_port = None
        # try to find operation in wsdl file
        for service_name, service in services.iteritems():
            for port_name, port in [port for port in service['ports'].items()]:
                if port['soap_ver'] == soap_ver:
                    service_port = service_name, port_name
                    operation = port['operations'].get(method)
                    if not operation:
                        raise RuntimeError('Operation %s not found in WSDL: '
                                           'Service/Port Type: %s' %
                                           (method, service_port))
                    return operation

        raise RuntimeError('Cannot determine service in WSDL: '
                           'SOAP version: %s' % soap_ver)

    output = get_operation()['output']
    resp = response('Body', ns=SOAPENV).children().unmarshall(output, strict=True)

    return resp[output.keys()[0]]

