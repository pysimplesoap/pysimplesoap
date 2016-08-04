#!/usr/bin/python
import unittest
from unittest import defaultTestLoader
import sys
import logging
import test_pysimplesoap


if __name__ == '__main__':
    FORMAT = "%(asctime)s %(levelname)6s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%m%d%H%M%S', stream=sys.stdout)
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromModule(test_pysimplesoap))
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(-1)
