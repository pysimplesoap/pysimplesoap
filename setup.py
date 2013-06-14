#!/usr/bin/env python

import setuptools
from distutils.core import setup
try:
    import py2exe
    from nsis import build_installer
except:
    build_installer = None

from pysimplesoap import __version__, __author__, __author_email__, __license__

setup(
    name='PySimpleSOAP',
    version=__version__,
    description='Python Simple SOAP Library',
    author=__author__,
    author_email=__author_email__,
    url='http://code.google.com/p/pysimplesoap',
    packages=['pysimplesoap'],
    license=__license__,
    console=['client.py'],
    cmdclass={"py2exe": build_installer},
)
