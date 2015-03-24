import unittest
from unittest.mock import patch
import sys

class MockData(object):
    def decode(self, type):
        return "mock text"

class MockResponse(object):
    def __init__(self, status=None, reason=None, headers=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.data = MockData()

class MockPoolManager(object):
    def __init__(self, timeout=None, num_pools=10, maxsize=None, headers=None, 
                 status=None, retries=None):
        self.timeout = None
        self.num_pools = num_pools
        self.headers = headers
        
    def urlopen(self, method=None, url=None, headers=None, body=None):
        return MockResponse(
            status=headers.get('status', None),
            reason=headers.get('reason', None),
            headers=headers)

    def clear(self):
        pass

class MockHTTPError(Exception):
    def __init__(self, message=None, errors=None):
        self.message = message
        self.errors = errors

class MockExceptions(object):
    HTTPError = MockHTTPError

class MockUtil(object):
    def make_headers(basic_auth=None):
        return {}

class MockUrllib3(object):
    __version__ = 1.0
    def PoolManager(self, timeout=None, num_pools=None, headers=None, 
                    maxsize=None, retries=None):
        return MockPoolManager(timeout=timeout, num_pools=num_pools, 
                               maxsize=maxsize, headers=headers)

class TestUrllib3Transport(unittest.TestCase):
    def test_send(self):
        sys.modules['urllib3'] = MockUrllib3()
        sys.modules['urllib3.exceptions'] = MockExceptions()
        sys.modules['urllib3.util'] = MockUtil()
        from pysimplesoap.transport import urllib3Transport
        headers = {
            'status': 200,
            'reason': 'OK'
        }
        http = urllib3Transport(num_pools=10, timeout=2.0, headers=headers)
        header, content = http.request('', headers=headers)
        self.assertEqual('mock text', content)
        
        headers['status'] = 404
        headers['reason'] = 'not found'
        http = urllib3Transport(num_pools=10, timeout=2.0, headers=headers)
        try:
            http.request('', headers=headers)
        except MockHTTPError:
            pass
        except:
            self.fail("Unexpected exception thrown")

        try:
            http.close()
        except Exception as e:
            self.fail("Unexpected exception thrown")


