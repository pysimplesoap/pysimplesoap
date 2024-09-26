# pysimplesoap/__init__.py

__version__ = "1.16.3"
__author__ = "Mariano Reingart"
__author_email__ = "reingart@gmail.com"
__license__ = "LGPL 3.0"
__description__ = "Python simple and lightweight SOAP library"
__url__ = "https://github.com/diegonaranjo/pysimplesoap"

# Nuevo campo para contribuidores
__contributors__ = [
    "Diego Naranjo <diego.s.naranjo@gmail.com>",
]

# Importa los módulos principales para facilitar su uso
from . import client, server, simplexml, transport