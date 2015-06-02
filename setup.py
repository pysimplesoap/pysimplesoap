#!/usr/bin/env python

from setuptools import setup
import os
import subprocess
import sys
import warnings

try:
    import py2exe
    from nsis import build_installer
except:
    build_installer = None

#from aiopss import __version__, __author__, __author_email__, __license__
# convert the README and format in restructured text (only when registering)
long_desc = ""
if os.path.exists("README.md") and sys.platform == "linux2":
    try:
        cmd = ['pandoc', '--from=markdown', '--to=rst', 'README.md']
        long_desc = subprocess.check_output(cmd).decode("utf8")
        print("Long DESC", long_desc)
    except Exception as e:
        warnings.warn("Exception when converting the README format: %s" % e)


setup(
    name='aiopss',
    version=1.16,
    description='Python simple and lightweight SOAP Library',
    long_description=long_desc,
    url='http://code.google.com/p/pysimplesoap',
    packages=['aiopss'],
    install_requires=['aiohttp'],
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
