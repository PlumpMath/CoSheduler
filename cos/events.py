# encoding: utf-8



log = __import__('logging').getLogger(__name__)
__all__ = []



class Event(object):
    __str__     = lambda self: self.__class__.__name__
    __repr__    = lambda self: self.__class__.__name__









"""

class SpawnEvent(Event):
    def __init__(self, task):
        self.task = task
    
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.task)


class FinishedEvent(Event):
    pass


class ReadyEvent(Event):
    pass


class FinishedEvent(Event):
    pass


class NoOpEvent(Event):
    pass


class ContinueEvent(Event):
    def __init__(self, when, priority=PRIORITY_NORMAL):
        super(ContinueEvent, self).__init__()
        
        self.when = when
        self.priority = priority
    
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.when)


class LogEvent(Event):
    pass


class IOEvent(Event):
    def __init__(self, name, value):
        self.name, self.value = name, value
    
    def __repr__(self):
        return "%s = %r" % (self.name, self.value)


class OutputChangedEvent(IOEvent):
    pass


class InputChangedEvent(IOEvent):
    pass
"""