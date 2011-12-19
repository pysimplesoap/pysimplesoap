# coding: utf-8

import unittest

def add(suite, module):
    suite.addTest(unittest.TestLoader().loadTestsFromModule(module))

def test():
    # TODO: automagicaly import modules test/*_test.py
    from tests import soapdispatcher_test
    from tests import simplexmlelement_test
    
    suite = unittest.TestSuite()
    
    add(suite, soapdispatcher_test)
    add(suite, simplexmlelement_test)
    
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    test()
