import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class DummyHTTP:
    def __init__(self, xml_response):
        self.xml_response = xml_response
    def request(self, location, method, body, headers):
        print method, location
        print headers
        print body
        return {}, self.xml_response


