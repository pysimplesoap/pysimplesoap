''' API module for functional usage like encode/decode '''
import xmltodict
from xml.parsers.expat import ExpatError
from .wsdl import parse
from .simplexml import SimpleXMLElement
from .errors import SoapFault
from .env import SOAP_NAMESPACES

__all__ = ('decode', )


def decode(headers, content, wsdl_or_services, ns='soapenv', method=None):
    parser = _SoapMsgParser(wsdl_or_services, ns, method)
    return parser.parse(headers, content)


class _SoapMsgParser(object):
    def __init__(self, wsdl_or_services, ns='soapenv', method=None):
        if type(wsdl_or_services) in (str, unicode):
            _, _, _, _, self.services = parse(wsdl_or_services)
        else:
            self.services = wsdl_or_services
        self.soap_version = ns.startswith('soap12') and 'soap12' or 'soap11'
        self.namespace = SOAP_NAMESPACES[ns]
        self.method = method

    def parse(self, headers, content):
        content_type = headers and headers.get('content-type', '') or ''
        raw_xml, mimes = self._get_raw_xml(content_type, content)
        resp = self._parse_raw_xml(raw_xml, self.method or headers['soapaction'].strip('"').rsplit('/', 1)[1])
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
            start_pos = raw_xml.find('\r\n\r\n')+4
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
        if response("Fault", ns=SOAP_NAMESPACES.values(), error=False):
            self._raise_fault(response, operation)
        input_output = operation['input']
        input_output.update(operation['output'])
        resp = response('Body', ns=self.namespace) \
                .children() \
                .unmarshall(input_output, strict=True) \
                .values()[0]

        return resp

    def _raise_fault(self, response, operation):
        detail_xml = response("detail", ns=SOAP_NAMESPACES.values(), error=False)
        detail = None

        if detail_xml and detail_xml.children():
            if self.services is not None:
                fault_name = detail_xml.children()[0].get_name()
                # if fault not defined in WSDL, it could be an axis or other
                # standard type (i.e. "hostname"), try to convert it to string
                fault = operation['faults'].get(fault_name) or unicode
                detail = detail_xml.children()[0].unmarshall(fault, strict=False)
            else:
                detail = repr(detail_xml.children())

        raise SoapFault(unicode(response.faultcode),
                        unicode(response.faultstring),
                        detail)

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

