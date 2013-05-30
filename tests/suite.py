# -*- coding: utf-8 -*-

import unittest


def add(suite, module):
    suite.addTest(unittest.TestLoader().loadTestsFromModule(module))


def test():
    # TODO: automagicaly import modules test/*_test.py
    from . import soapdispatcher_test
    from . import simplexmlelement_test
    from . import issues_tests
    from . import afip_tests
    from . import server_multins_test
    # licencias_tests is for internal use, wsdl is not published
    # from . import licencias_tests
    # from . import trazamed_tests

    suite = unittest.TestSuite()

    add(suite, soapdispatcher_test)
    add(suite, simplexmlelement_test)
    add(suite, issues_tests)
    add(suite, afip_tests)
    add(suite, server_multins_test)
    ##add(suite, licencias_tests)
    ##add(suite, trazamed_tests)

    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    test()
