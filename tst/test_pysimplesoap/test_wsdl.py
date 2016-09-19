import os
from .base import BaseTestcase
from pysimplesoap.wsdl import parse


class TestWsdlParsing(BaseTestcase):
    def test_with_import_and_multiservices(self):
        _, _, _, _, services = parse(os.path.abspath('tst/data/ne3s.wsdl'))
        self.assertEqual(services['NE3SBasicNotificationsService']['documentation'], '')
        self.assertEqual(services['NE3SBasicNotificationsService']['ports']['ne3sBasicNotifications']['operations']['transferNotification']['output']['transferNotificationResponse']['managerRegistrationId'], str)
        self.assertEqual(services['NE3SBulkOperationsService']['ports']['ne3sBulkOperations']['operations']['upload']['input']['upload']['sessionId'], str)
        self.assertEqual(services['NE3SBulkOperationsService']['ports']['ne3sBulkOperations']['operations']['upload']['input']['upload']['filter']['uploadType'], str)

    def test_with_fd(self):
        with open('tst/data/ne3s.wsdl') as fp:
            _, _, _, _, services = parse(fp, os.path.abspath('tst/data'))
        self.assertEqual(services['NE3SBasicNotificationsService']['documentation'], '')
        self.assertEqual(services['NE3SBasicNotificationsService']['ports']['ne3sBasicNotifications']['operations']['transferNotification']['output']['transferNotificationResponse']['managerRegistrationId'], str)
        self.assertEqual(services['NE3SBulkOperationsService']['ports']['ne3sBulkOperations']['operations']['upload']['input']['upload']['sessionId'], str)

    def test_with_stringio(self):
        with open('tst/data/ne3s.wsdl') as fp:
            content = fp.read()
        from cStringIO import StringIO
        fp = StringIO()
        fp.write(content)
        fp.seek(0)
        _, _, _, _, services = parse(fp, os.path.abspath('tst/data'))
        self.assertEqual(services['NE3SBasicNotificationsService']['documentation'], '')
        self.assertEqual(services['NE3SBasicNotificationsService']['ports']['ne3sBasicNotifications']['operations']['transferNotification']['output']['transferNotificationResponse']['managerRegistrationId'], str)
        self.assertEqual(services['NE3SBulkOperationsService']['ports']['ne3sBulkOperations']['operations']['upload']['input']['upload']['sessionId'], str)

