''' API module for functional usage like encode/decode '''
import xmltodict
from xml.parsers.expat import ExpatError
from .wsdl import parse
from .simplexml import SimpleXMLElement

__all__ = ('decode', )


def decode(headers, content, wsdl, soap_ver='soap11'):
    parser = _SoapMsgParser(wsdl, soap_ver)
    return parser.parse(headers, content)


SOAPENV = 'http://schemas.xmlsoap.org/soap/envelope/'

class _SoapMsgParser(object):
    def __init__(self, wsdl, soap_ver='soap11'):
        self.elements, self.messages, self.port_types, self.bindings, self.services = parse(wsdl)
        self.soap_version = soap_ver

    def parse(self, headers, content):
        content_type = headers and headers.get('content-type', '') or ''
        raw_xml, mimes = self._get_raw_xml(content_type, content)
        resp = self._parse_raw_xml(raw_xml, headers['soapaction'].strip('"').rsplit('/', 1)[1])
        resp.update(self._parse_mimes(mimes))

        return resp

    def _get_raw_xml(self, content_type, text):
        settings = self._parse_content_type(content_type)

        if settings.get('multipart/related', False):
            boundary = '--' + settings['boundary']
            mimes = filter(lambda x: x not in ('', '--'), [e.strip() for e in text.split(boundary)])
            if not mimes:
                return '', []

            raw_xml = mimes.pop(0)
            start_pos = raw_xml.find(settings['start'])+len(settings['start'])
            raw_xml = raw_xml[start_pos:].strip()

            return raw_xml, mimes

        return text, []

    def _parse_content_type(self, content_type):
        settings = {}
        for item in content_type.split(';'):
            if '=' in item:
                k, v = item.strip().split('=', 1)
                settings[k] = v.strip('""')
            else:
                settings[item.strip()] = True

        return settings

    def _parse_raw_xml(self, raw_xml, method):
        response = SimpleXMLElement(raw_xml)
        operation = self._get_operation(method)
        input_output = operation['input']
        input_output.update(operation['output'])
        resp = response('Body', ns=SOAPENV) \
                .children() \
                .unmarshall(input_output, strict=True) \
                .values()[0]

        return resp

    def _parse_mimes(self, mimes):
        return dict([self._parse_one_mime(mime) for mime in mimes])

    def _parse_one_mime(self, mime):
        cid_start = mime.find('Content-ID:') + len('Content-ID:')
        cid_end = mime.find('\r\n', cid_start)
        cid = mime[cid_start:cid_end].strip('< >')
        content = mime[mime.find('\r\n\r\n', cid_end):].strip()

        try:
            return cid, xmltodict.parse(content)
        except ExpatError:
            return cid, content

    def _get_operation(self, method):
        for service_name, service in self.services.iteritems():
            for port_name, port in service['ports'].iteritems():
                if port['soap_ver'] == self.soap_version:
                    if method in port['operations']:
                        return port['operations'][method]

        raise RuntimeError('Cannot determine service in WSDL: '
                           'SOAP version: %s' % self.soap_version)

