import os
from unittest import TestCase

TEST_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))


class BaseTestcase(TestCase):
    def get_data(self, file_name):
        abs_file_path = os.path.join(TEST_DATA_PATH, file_name+'.txt')
        if os.path.exists(abs_file_path):
            with open(abs_file_path, 'rb') as fp:
                return fp.read()
        raise RuntimeError('file "%s" does not exist' % file_name)
