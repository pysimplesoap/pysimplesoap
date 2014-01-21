# -*- coding: utf-8 -*-

import unittest


def add(suite, module):
    suite.addTest(unittest.TestLoader().loadTestsFromModule(module))


def test():
    # TODO: automagicaly import modules test/*_test.py
    from . import soapdispatcher_test
    from . import simplexmlelement_test
    from . import issues_test
    from . import afip_test
    from . import server_multins_test
    # licencias_tests is for internal use, wsdl is not published
    # from . import licencias_test
    # from . import trazamed_test
    from . import cfdi_mx_test
    from . import sri_ec_test
    from . import nfp_br_test

    suite = unittest.TestSuite()

    add(suite, soapdispatcher_test)
    add(suite, simplexmlelement_test)
    add(suite, issues_test)
    add(suite, afip_test)
    add(suite, server_multins_test)
    ##add(suite, licencias_test)
    ##add(suite, trazamed_test)
    add(suite, cfdi_mx_test)
    add(suite, sri_ec_test)
    add(suite, nfp_br_test)

    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    test()
