#!/usr/bin/env python

from distutils.core import setup
try:
    import py2exe
    from nsis import build_installer
except:
    build_installer = None

from pysimplesoap import __version__, __author__, __author_email__, __license__

# in the transition, register both:
for name in ('soap2py', 'PySimpleSOAP'):
    setup(
        name=name,
        version=__version__,
        description='Python simple and lightweight SOAP Library',
        author=__author__,
        author_email=__author_email__,
        url='http://code.google.com/p/pysimplesoap',
        packages=['pysimplesoap'],
        license=__license__,
    #    console=['client.py'],
        cmdclass={"py2exe": build_installer},
        classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
            "Topic :: Communications",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )
