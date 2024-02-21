import socket
import unittest

from pysimplesoap.transport import Httplib2Transport


class TestHttplib2TransportTransportTimeout(unittest.TestCase):
    def setUp(self):
        # url that delays 2 seconds before returning
        self.url = "https://httpbin.org/delay/2"

    def test_timeout(self):
        transport = Httplib2Transport(timeout=1)

        with self.assertRaises(socket.timeout):
            transport.request(self.url)

    def test_no_timeout(self):
        transport = Httplib2Transport(timeout=None)

        response, _ = transport.request(self.url)
        self.assertEqual(response.status, 200)


if __name__ == "__main__":
    unittest.main()
