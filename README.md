PySimpleSOAP / soap2py
======================

Python simple and lightweight SOAP library for client and server webservices interfaces, aimed to be as small and easy as possible, supporting most common functionality.
Initially it was inspired by [PHP Soap Extension](http://php.net/manual/en/book.soap.php) (mimicking its functionality, simplicity and ease of use), with many advanced features added.

This is a **Stable Branch** ("stable_py3k")
mainly to be used with [https://github.com/reingart/pyafipws/tree/py3k]() under
Python 3

Changelog
---------

Last features (2014-2017):

 * Add ns prefix for new server type '.net' (in clients)
 * Fix special cases of array marshalling (scalar, complex, etc., "jetty style")
 * Add type information to marshalling (used to convert parmeters in webservice calls)
 * Base64 binary support (unmarshalling)
 * Handle missing cache folder and clenaups (avoid exceptions if no write permissions)
 * Fix version number to comply with PEP 440 and pypi...
 * TLSv1.2 and graceful fallback
 * Avoid fallback to obsolete SSLv3
 * Workaround for broken SSLv3/TLSv1 server negotiation
 * fixed PyCURL GnuTLS recv error (-9). ubuntu 14.04 and AFIP .NET

Goals
-----

 * Simple: less than 200LOC client/server concrete implementation for easy maintainability and enhancments.
 * Flexible: adapted to several SOAP dialects/servers (Java Axis, .Net, WCF, JBoss, "jetty"), with the posibility of fine-tuning XML request and responses
 * Pythonic: no artifacts, no class generation, no special types, RPC calls parameters and return values are simple python structures (dicts, list, etc.)
 * Dynamic: no definition (WSDL) required, dynamic generation and parsing supported (cached in a pickle file for performance, supporting fixing broken WSDL)
 * Easy: simple xml manipulation, including basic serialization and raw object-like access to SOAP messages
 * Extensible: supports several HTTP wrappers (httplib2, pycurl, urllib2) for special transport needs over SSL and proxy (ISA)
 * WSGI compilant: server dispatcher can be integrated to other python frameworks (web2py, django, etc.)
 * Backwards compatible: stable API, no breaking changes between releases
 * Lightweight: low memory footprint and fast processing (an order of magnitude in some situations, relative to other implementations)

History
-------

Client initially developed for AFIP (Argentina's IRS) web services: electronic invoice, tax bonus, insurance, foreign trade, agriculture, customs, etc. (http://code.google.com/p/pyafipws/wiki/ProjectSummary)

Now it has been extended to support other webservices like Currency Exchange Control and TrazaMed (National Traceability of Medical Drugs Program)

Also, includes Server side support (a generic dispatcher, in order to be exposed from web2py service framework, adaptable to other webservers, including examples for standalone WSGI and django)

Source Code originally available on [GoogleCode](https://code.google.com/p/pysimplesoap)


Testing
-------

     python -m unittest discover -s tests -p "*_test.py"

Support
-------

For community support, please fell free to fill an [issue](https://github.com/pysimplesoap/pysimplesoap/issues/new) or send an email to [soap@python.org](https://mail.python.org/mailman/listinfo/soap).
Please do not add comment to wiki pages if you have technical questions.

For priority commercial technical support, you can contact [Mariano Reingart](mailto:reingart@gmail.com) (project creator and main maintainer).
