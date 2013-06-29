# coding: utf-8

import datetime
import unittest
from pysimplesoap.simplexml import SimpleXMLElement

class TestSimpleXMLElement(unittest.TestCase):
    def eq(self, value, expectation, msg=None):
        if msg is not None:
            msg += ' %s' % value
            self.assertEqual(value, expectation, msg)
        else:
            self.assertEqual(value, expectation, value)
    
    def test_attributes_access(self):
        span = SimpleXMLElement('<span><a href="python.org.ar">pyar</a><prueba><i>1</i><float>1.5</float></prueba></span>')
        text = "pyar"
        self.eq(str(span.a), text, 'Access by __getattr__:')
        self.eq(str(span.a), text, 'Access by __getattr__:')
        self.eq(str(span('a')), text, 'Access by __call__:')
        self.eq(str(span.a(0)), text, 'Access by __call__ on attribute:')
        self.eq(span.a['href'], "python.org.ar", 'Access by __getitem__:')
        self.eq(int(span.prueba.i), 1, 'Casting to int:')
        self.eq(float(span.prueba.float), 1.5, 'Casting to float:')
        
    def test_to_xml(self):
        xml = '<?xml version="1.0" encoding="UTF-8"?><span><a href="python.org.ar">pyar</a><prueba><i>1</i><float>1.5</float></prueba></span>'
        self.eq(SimpleXMLElement(xml).as_xml(), xml)
        
        xml = '<?xml version="1.0" encoding="UTF-8"?><span><a href="google.com">google</a><a>yahoo</a><a>hotmail</a></span>'
        self.eq(SimpleXMLElement(xml).as_xml(), xml)
        
    def test_unmarshall(self):
        span = SimpleXMLElement('<span><name>foo</name><value>3</value></span>')
        d = {'span': {'name': str, 'value': int}}
        e = {'span': {'name': 'foo', 'value': 3}}
        self.eq(span.unmarshall(d), e)
        
        span = SimpleXMLElement('<span><name>foo</name><name>bar</name></span>')
        d = {'span': [{'name': str}]}
        e = {'span': [{'name': 'foo'}, {'name': 'bar'}]}
        self.eq(span.unmarshall(d), e)
        
        span = SimpleXMLElement('<activations><items><number>01234</number><status>1</status></items><items><number>04321</number><status>0</status></items></activations>')
        d = {'activations': [
                {'items': {
                    'number': str,
                    'status': int
                }}
            ]}
        
        e = {'activations': [{'items': {'number': '01234', 'status': 1}}, {'items': {'number': '04321', 'status': 0}}]}
        self.eq(span.unmarshall(d), e)

    def test_adv_unmarshall(self):
        xml = """
        <activations>
            <items>
                <number>01234</number>
                <status>1</status>
                <properties>
                    <name>foo</name>
                    <value>3</value>
                </properties>
                <properties>
                    <name>bar</name>
                    <value>4</value>
                </properties>
            </items>
            <items>
                <number>04321</number>
                <status>0</status>
            </items>
        </activations>
        """
        span = SimpleXMLElement(xml)
        d = {'activations': [
                {'items': {
                    'number': str,
                    'status': int,
                    'properties': ({
                        'name': str,
                        'value': int
                    }, )
                }}
            ]}

        e = {'activations': [
                {'items': {'number': '01234', 'status': 1, 'properties': ({'name': 'foo', 'value': 3}, {'name': 'bar', 'value': 4})}}, 
                {'items': {'number': '04321', 'status': 0}}
            ]}
        self.eq(span.unmarshall(d), e)

    def test_tuple_unmarshall(self):
        xml = """
        <foo>
            <boo>
                <bar>abc</bar>
                <baz>1</baz>
            </boo>
            <boo>
                <bar>qwe</bar>
                <baz>2</baz>
            </boo>
        </foo>
        """
        span = SimpleXMLElement(xml)
        d = {'foo': {
                'boo': ({'bar': str, 'baz': int}, )
        }}

        e = {'foo': {
                'boo': (
                {'bar': 'abc', 'baz': 1},
                {'bar': 'qwe', 'baz': 2},
            )}}
        self.eq(span.unmarshall(d), e)
        
        
    def test_basic(self):
        span = SimpleXMLElement('<span><a href="python.org.ar">pyar</a><prueba><i>1</i><float>1.5</float></prueba></span>')
        span1 = SimpleXMLElement('<span><a href="google.com">google</a><a>yahoo</a><a>hotmail</a></span>')
        self.eq([str(a) for a in span1.a()], ['google', 'yahoo', 'hotmail'])
        
        span1.add_child('a','altavista')
        span1.b = "ex msn"
        d = {'href':'http://www.bing.com/', 'alt': 'Bing'} 
        span1.b[:] = d
        self.eq(sorted([(k,v) for k,v in span1.b[:]]), sorted(d.items()))
        
        xml = '<?xml version="1.0" encoding="UTF-8"?><span><a href="google.com">google</a><a>yahoo</a><a>hotmail</a><a>altavista</a><b alt="Bing" href="http://www.bing.com/">ex msn</b></span>'
        self.eq(span1.as_xml(), xml)
        self.assertTrue('b' in span1)
        
        span.import_node(span1)
        xml = '<?xml version="1.0" encoding="UTF-8"?><span><a href="python.org.ar">pyar</a><prueba><i>1</i><float>1.5</float></prueba><span><a href="google.com">google</a><a>yahoo</a><a>hotmail</a><a>altavista</a><b alt="Bing" href="http://www.bing.com/">ex msn</b></span></span>'
        self.eq(span.as_xml(), xml)
        
        types = {'when': datetime.datetime}
        when = datetime.datetime.now()
        dt = SimpleXMLElement('<when>%s</when>' % when.isoformat())
        self.eq(dt.unmarshall(types)['when'], when)

if __name__ == '__main__':
    unittest.main()
