''' API module for functional usage like encode/decode '''
from .wsdl import parse


def decode(wsdl_path, headers, content):
    # TODO:
    services = parse(wsdl_path)
    return services

        # response = SimpleXMLElement(self.get_data('mime_with_xml_only'), headers=headers)
        # output = client.get_operation('startRegistration')['output']
        # resp = response('Body', ns=ns).children().unmarshall(output, strict=True)
