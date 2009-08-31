# encoding: utf-8

import types

__all__ = ['adict']


class adict(dict):
    """A dictionary with attribute-style access. It maps attribute access to the real dictionary."""
    
    def __init__(self, default=None, *args, **kw):
        #self._default = default().next if isinstance(default, types.GeneratorType) else default
        dict.__init__(self, *args, **kw)
    
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, super(adict, self).__repr__())
    
    def __delattr__(self, name):
        del self[name]
    
    def __getattr__(self, name):
        #if name not in self and self._default is not None:
        #    self[name] = self._default() if callable(self._default) else self._default
        
        return self[name]
    
    def __setattr__(self, name, value):
        self[name] = value

