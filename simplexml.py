#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Simple XML manipulation"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008/009 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.0"

import xml.dom.minidom


DEBUG = False


class SimpleXMLElement(object):
    "Simple XML manipulation (simil PHP)"
    
    def __init__(self, text = None, elements = None, document = None, namespace = None, prefix=None):
        self.__ns = namespace
        self.__prefix = prefix
        if text:
            try:
                self.__document = xml.dom.minidom.parseString(text)
            except:
                if DEBUG: print text
                raise
            self.__elements = [self.__document.documentElement]
        else:
            self.__elements = elements
            self.__document = document
    
    def addChild(self,name,text=None,ns=True):
        "Adding a child tag to a node"
        if not ns or not self.__ns:
            if DEBUG: print "adding %s" % (name)
            element = self.__document.createElement(name)
        else:
            if DEBUG: print "adding %s ns %s %s" % (name, self.__ns,ns)
            if self.__prefix:
                element = self.__document.createElementNS(self.__ns, "%s:%s" % (self.__prefix, name))
            else:
                element = self.__document.createElementNS(self.__ns, name)
        if text:
            if isinstance(text, unicode):
                element.appendChild(self.__document.createTextNode(text))
            else:
                element.appendChild(self.__document.createTextNode(str(text)))
        self.__element.appendChild(element)
        return SimpleXMLElement(
                    elements=[element],
                    document=self.__document,
                    namespace=self.__ns,
                    prefix=self.__prefix)
    
    def __setattribute__(self, name, text):
        "Add text child tag node (short form)"
        self.addChild(name,text)

    def addComment(self, data):
        "Add an xml comment to this child"
        comment = self.__document.createComment(data)
        self.__element.appendChild(comment)

    def asXML(self,filename=None,pretty=False):
        "Return the XML representation of the document"
        if not pretty:
            return self.__document.toxml('UTF-8')
        else:
            return self.__document.toprettyxml(encoding='UTF-8')

    def __repr__(self):
        "Return the XML representation of this tag"
        return self.__element.toxml('UTF-8')

    def getName(self):
        "Return the tag name of this node"
        return self.__element.tagName

    def getLocalName(self):
        "Return the tag loca name (prefix:name) of this node"
        return self.__element.localName

    def getPrefix(self):
        "Return the namespace prefix of this node"
        return self.__element.prefix

    def attributes(self):
        "Return a dict of attributes for this tag"
        #TODO: use slice syntax [:]?
        return self.__element.attributes

    def addAttribute(self, name, value):
        "Set an attribute value from a string"
        #TODO: use __setitem__?
        self.__element.setAttribute(name, value)
     
    def __getattr__(self, name):
        "Search (even in child nodes) and return a child tag by name"
        try:
            if self.__ns:
                if DEBUG: print "searching %s by ns=%s" % (name,self.__ns)
                elements = self.__elements[0].getElementsByTagNameNS(self.__ns, name)
            if not self.__ns or not elements:
                if DEBUG: print "searching %s " % (name)
                elements = self.__elements[0].getElementsByTagName(name)
            if not elements:
                if DEBUG: print self.__elements[0].toxml()
                raise AttributeError("Sin elementos")
            return SimpleXMLElement(
                elements=elements,
                document=self.__document,
                namespace=self.__ns,
                prefix=self.__prefix)
        except AttributeError, e:
            raise AttributeError("Tag not found: %s (%s)" % (name, str(e)))

    def __iter__(self):
        "Iterate over xml tags at this level"
        try:
            for __element in self.__elements:
                yield SimpleXMLElement(
                    elements=[__element],
                    document=self.__document,
                    namespace=self.__ns,
                    prefix=self.__prefix)
        except:
            raise

    def __getitem__(self,item):
        "Return xml tag (by name o numerical index)"
        #TODO: use string names for real tag attributes?
        if isinstance(item, basestring):
            return getattr(self,item)
        else:
            return SimpleXMLElement(
                elements=[self.__elements[item]],
                document=self.__document,
                namespace=self.__ns,
                prefix=self.__prefix)

    def __dir__(self):
        "List xml children tags names"
        return [node.tagName for node 
                in self.__element.childNodes
                if node.nodeType != node.TEXT_NODE]

    def children(self):
        "Return xml children tags element"
        return SimpleXMLElement(
                elements=[__element for __element in self.__element.childNodes
                          if __element.nodeType == __element.ELEMENT_NODE],
                document=self.__document,
                namespace=self.__ns,
                prefix=self.__prefix)

    def __contains__( self, item):
        "Search for a tag name in this element or child nodes"
        return self.__element.getElementsByTagName(item)
    
    def __unicode__(self):
        "Returns the unicode text nodes of the current element"
        if self.__element.childNodes:
            rc = u""
            for node in self.__element.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc = rc + node.data
            return rc
        return ''
    
    def __str__(self):
        "Returns the str text nodes of the current element"
        return unicode(self).encode("utf8","ignore")

    def __int__(self):
        "Returns the integer value of the current element"
        return int(self.__str__())

    def __float__(self):
        "Returns the float value of the current element"
        try:
            return float(self.__str__())
        except:
            raise IndexError(self.__element.toxml())    
    
    __element = property(lambda self: self.__elements[0])

    def unmarshall(self, types):
        "Convert to python values the current serialized xml element"
        # types is a dict of {tag name: convertion function}
        # example: types={'p': {'a': int,'b': int}, 'c': [{'d':str}]}
        #   expected xml: <p><a>1</a><b>2</b></p><c><d>hola</d><d>chau</d>
        #   returnde value: {'p': {'a':1,'b':2}, `'c':[{'d':'hola'},{'d':'chau'}]}
        d = {}
        for node in self:
            name = str(node.getLocalName())
            try:
                fn = types[name]
            except (KeyError, ), e:
                raise TypeError("Tag: %s invalid" % (name,))
            if isinstance(fn,list):
                value = []
                for child in node.children():
                    value.append(child.unmarshall(fn[0]))
            elif isinstance(fn,dict):
                value = node.children().unmarshall(fn)
            else:
                if str(node) or fn == str:
                    try:
                        value = fn(str(node))
                    except (ValueError, TypeError), e:
                        raise ValueError("Tag: %s: %s" % (name, unicode(e)))
                else:
                    value = None
            d[name] = value
        return d

    def marshall(self, name, value, add_child=True, add_comments=False, ns=False):
        "Analize python value and add the serialized XML element using tag name"
        if isinstance(value, dict):  # serialize dict (<key>value</key>)
            child = add_child and self.addChild(name,ns=ns) or self
            for k,v in value.items():
                child.marshall(k, v, add_comments=add_comments, ns=ns)
        elif isinstance(value, tuple):  # serialize tuple (<key>value</key>)
            child = add_child and self.addChild(name,ns=ns) or self
            for k,v in value:
                getattr(self,name).marshall(k, v, add_comments=add_comments, ns=ns)
        elif isinstance(value, list): # serialize lists
            child=self.addChild(name,ns=ns)
            if add_comments:
                child.addComment("Repetitive array of:")
            for t in value:
                child.marshall(name,t, False, add_comments=add_comments, ns=ns)
        elif isinstance(value, basestring): # do not convert strings or unicodes
            self.addChild(name,value,ns=ns)
        elif value is None: # sent a empty tag?
            self.addChild(name,ns=ns)
        elif value in (int, str, float, bool, unicode):
            # add commented placeholders for simple tipes (for examples/help only)
            type_map={str:'string',unicode:'string',
                      bool:'boolean',int:'integer',float:'float'}
            child = self.addChild(name,ns=ns) 
            child.addComment(type_map[value])
        else: # the rest of object types are converted to string 
            self.addChild(name,str(value),ns=ns) # check for a asXML?


if __name__ == "__main__":
    span = SimpleXMLElement('<span><a href="google.com">google</a><prueba><i>1</i><float>1.5</float></prueba></span>')
    print str(span.a)
    print int(span.prueba.i)
    print float(span.prueba.float)

    span = SimpleXMLElement('<span><a href="google.com">google</a><a>yahoo</a><a>hotmail</a></span>')
    for a in span.a:
        print str(a)

    span.addChild('a','altavista')
    print span.asXML()