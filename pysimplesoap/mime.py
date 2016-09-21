import mimetypes
import uuid
from cStringIO import StringIO


class MimeGenerator(object):
    def __init__(self, xml, attachments):
        self._xml = xml
        self._attachments = attachments
        self._boundary = str(uuid.uuid1())
        self._file = StringIO()

    def get_boundary(self):
        return self._boundary

    def generate(self):
        self._write_first_boundary()
        self._write_xml()
        self._write_attachments()
        self._write_last_boundary()

        return self

    def to_string(self):
        self._file.seek(0)
        return self._file.read()

    def _write_first_boundary(self):
        self._file.write('--'+self._boundary+'\r\n')

    def _write_xml(self):
        self._file.write('Content-Type: text/xml\r\n\r\n') # header
        self._file.write(self._xml) # body

    def _write_attachments(self):
        for attach in self._attachments:
            self._write_boundary()
            self._write_one_attachment(attach)

    def _write_boundary(self):
        self._file.write('\r\n--'+self._boundary+'\r\n')

    def _write_one_attachment(self, attach):
        cid, path_or_content = attach
        self._file.write('Content-Id:<%s>\r\n' % cid) # header
        self._file.write('Content-Type: %s\r\n' % self._get_content_type(path_or_content)) # header
        self._file.write('Content-Transfer-Encoding: bindary\r\n\r\n') # header
        self._file.write(self._get_attachment_content(path_or_content)) # body

    def _get_content_type(self, path_or_content):
        if path_or_content.startswith('file://'):
            content_type, _ = mimetypes.guess_type(path_or_content.split('file://', 1)[0])
            if content_type:
                return content_type
        return 'application/octet-stream'

    def _get_attachment_content(self, path_or_content):
        # handle cid is a file
        if path_or_content.startswith('file://'):
            with open(path_or_content.split('file://', 1)[1], 'rb') as fp:
                return fp.read()
        return path_or_content

    def _write_last_boundary(self):
        self._file.write('\r\n--'+self._boundary+'--')

