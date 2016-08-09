import sys

class SoapFault(RuntimeError):
    def __init__(self, faultcode, faultstring, detail=None):
        self.faultcode = faultcode
        self.faultstring = faultstring
        self.detail = detail
        RuntimeError.__init__(self, faultcode, faultstring, detail)

    def __unicode__(self):
        return '%s: %s' % (self.faultcode, self.faultstring)

    if sys.version > '3':
        __str__ = __unicode__
    else:
        def __str__(self):
            return self.__unicode__().encode('ascii', 'ignore')

    def __repr__(self):
        return "SoapFault(faultcode = %s, faultstring %s, detail = %s)" % (repr(self.faultcode),
                                                                           repr(self.faultstring),
                                                                           repr(self.detail))
