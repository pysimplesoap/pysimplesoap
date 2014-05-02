#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Brazil - Sao Paulo "Electronic Invoice"  (Nota Fiscal Paulista)"""

from __future__ import unicode_literals

from decimal import Decimal
import os
import unittest
from pysimplesoap.client import SoapClient, SoapFault, SimpleXMLElement

import sys
if sys.version > '3':
    basestring = str
    long = int

# Documentation: http://www.nfp.fazenda.sp.gov.br/MIWSCF.pdf
WSDL = 'https://www.nfp.fazenda.sp.gov.br/ws/arquivocf.asmx?WSDL'

HEADER_XML = """<Autenticacao Usuario="%s" Senha="%s" CNPJ="%s" 
                CategoriaUsuario="%d" xmlns="https://www.nfp.sp.gov.br/ws" />"""

# TODO: support attributes in headers / parameters

class TestNFP(unittest.TestCase):
 
    def test_enviar(self):
        "Prueba da envio de arquivos de cupons fiscais"
        
        # create the client webservice
        client = SoapClient(wsdl=WSDL, soap_ns="soap12env")
        # set user login credentials in the soap header: 
        client['Autenticacao'] = SimpleXMLElement(HEADER_XML % ("user","password", "fed_tax_num", 1))
        # call the webservice
        response = client.Enviar(NomeArquivo="file_name", ConteudoArquivo="content", EnvioNormal=True, Observacoes="")
        self.assertEqual(response['EnviarResult'], '206|CNPJ informado inv\xe1lido')            

    def test_consultar(self):
        "consulta ao resultado do processamento dos arquivos de cupons fiscai"
        # create the client webservice
        client = SoapClient(wsdl=WSDL, soap_ns="soap12env")
        # set user login credentials in the soap header: 
        client['Autenticacao'] = SimpleXMLElement(HEADER_XML % ("user","password", "fed_tax_num", 1))
        # call the webservice
        response = client.Consultar(Protocolo="")
        self.assertEqual(response['ConsultarResult'], '999|O protocolo informado n\xe3o \xe9 um n\xfamero v\xe1lido')

    def test_retificar(self):
        "Prueba da retifica de arquivos de cupons fiscais"
        
        # create the client webservice
        client = SoapClient(wsdl=WSDL, soap_ns="soap12env")
        # set user login credentials in the soap header: 
        client['Autenticacao'] = SimpleXMLElement(HEADER_XML % ("user","password", "fed_tax_num", 1))
        # call the webservice
        response = client.Retificar(NomeArquivo="file_name", ConteudoArquivo="content", EnvioNormal=True, Observacoes="")
        self.assertEqual(response['RetificarResult'], '206|CNPJ informado inv\xe1lido')
        
