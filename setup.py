#!/usr/bin/env python

from setuptools import setup, find_packages

# Importar la información de versión y metadatos desde __init__.py
from pysimplesoap import (
    __version__, __author__, __author_email__, __license__,
    __description__, __url__, __contributors__
)

# Leer el contenido de README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='PySimpleSOAP',
    version=__version__,
    packages=find_packages(),
    author=__author__,
    author_email=__author_email__,
    license=__license__,
    description=__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=__url__,
    install_requires=[
        'requests',
        'lxml',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.7',
    project_urls={
        'Source': __url__,
        'Tracker': f"{__url__}/issues",
    },
    # Agregar la información de los contribuidores
    extras_require={
        'Contributors': __contributors__,
    },
)