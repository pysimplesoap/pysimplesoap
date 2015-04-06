PySimpleSOAP / soap2py
======================

Python simple and lightweigh SOAP library for client and server webservices interfaces, aimed to be as small and easy as possible, supporting most common functionality.
Initially it was inspired by [PHP Soap Extension](http://php.net/manual/en/book.soap.php) (mimicking its functionality, simplicity and ease of use), with many advanced features added.

**Supports Python 3** (same codebase, no need to run 2to3)

Goals
-----

 * Simple: originally less than 200LOC client/server concrete implementation for easy maintainability and enhancements. 
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

Client initially developed for AFIP (Argentina's IRS) web services: electronic invoice, tax bonus, insurance, foreing trade, agriculture, customs, etc. (http://code.google.com/p/pyafipws/wiki/ProjectSummary)

Now it has been extended to support other webservices like Currency Exchange Control and TrazaMed (National Traceability of Medical Drugs Program)

Also, includes Server side support (a generic dispatcher, in order to be exposed from web2py service framework, adaptable to other webservers, including examples for standalone WSGI and django)

Source Code originally available on [GoogleCode](https://code.google.com/p/pysimplesoap)

Changelog
---------

Recent changes (2014/2015):

* Plug-in system to support for WSSE (Web-Services Security extensions)
* WSSE UsernameToken, UsernameDigestToken and BinaryTokenSignature support 
* Pythonic XML Security Library basic implementation (canonicalization, SHA1 hashing and RSA signing / verification using X509 digital certificates)
* Improved SOAP Fault details
* Several fixes (basic python3 support, CDATA, )

Ongoing efforts:

* Unit Tests update & clean up (removing old tests, better framework, fixing non-deterministic results, etc.) 
* WSDL advanced support (unifying nested elements structure dialects)
* Python3 support for WSSE XMLSec (M2Crypto alternatives?)
* Source code refactory to improve readability and maintainability

Previous contributed features (circa 2013, forked and merged back):

* Corrected support for multiple SOAP ports/bindings
* Support for both `import` and `include` stanzas in WSDL
* Support for a WSDL base directory to deal with relative pathnames in import/include stanzas
* Somewhat saner traceing/logging (traces now go to log.debug(), which you can handle per module)
* Somewhat more readable logic (by removing a bunch of helpers to a separate file)

Testing
-------

Using Python 2.7+:

    python -m unittest discover

Using older Python versions:

    python -m unittest tests/suite.py
  
Code coverage:

    sudo pip install coverage
    coverage run tests/suite.py
    coverage report -m 
    coverage html


Support
-------

For community support, please fell free to fill an [issue](https://github.com/pysimplesoap/pysimplesoap/issues/new) or send a email to [soap@python.org](https://mail.python.org/mailman/listinfo/soap).
Please do not add comment to wiki pages if you have technical questions.

For priority commercial technical support, you can contact [Mariano Reingart](mailto:reingart@gmail.com) (project creator and main maintainter, see [AUTHORS](AUTHORS.md) for more info).

