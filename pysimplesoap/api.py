''' API module for functional usage like encode/decode '''
from .wsdl import parse
from .simplexml import SimpleXMLElement


SOAPENV = 'http://schemas.xmlsoap.org/soap/envelope/'

def decode(headers, content, wsdl, soap_ver='soap11'):
    (elements, messages, port_types, bindings, services) = parse(wsdl)
    response = SimpleXMLElement(content, headers=headers)
    method = headers['soapaction'].strip('"').rsplit('/', 1)[1]

    def get_operation():
        # try to find operation in wsdl file
        for service_name, service in services.iteritems():
            for port_name, port in service['ports'].iteritems():
                if port['soap_ver'] == soap_ver:
                    if method in port['operations']:
                        return port['operations'][method]

        raise RuntimeError('Cannot determine service in WSDL: '
                           'SOAP version: %s' % soap_ver)

    operation = get_operation()
    input_output = operation['input']
    input_output.update(operation['output'])
    resp = response('Body', ns=SOAPENV).children().unmarshall(input_output, strict=True)

    return resp.values()[0]

