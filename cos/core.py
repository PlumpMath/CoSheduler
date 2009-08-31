# encoding: utf-8

import                                          cos

from uuid                                       import uuid4 as uuid

from cos.constants                              import PRIORITY_NORMAL


__all__ = ['Tasklet', 'Task', 'Routine']



class Tasklet(object):
    def __init__(self, task, priority=PRIORITY_NORMAL, parent=None):
        self.id = uuid()
        self.task = task
        self.priority = priority
        self.parent = parent
        self.messages = cos.queue.Queue()
    
    def __repr__(self):
        return "%r %s(%s)" % (self.task, self.__class__.__name__, self.id)
    
    def send(self, value):
        return self.task.send(value)
    
    def throw(self, type, value=None, traceback=None):
        return self.task.throw(type, value, traceback)


class Task(object):
    def __call__(self):
        raise NotImplementedError


class Routine(object):
    """An executable, system-level subroutine call."""
    
    def __init__(self, target=None):
        self.target = target
    
    def handle(self, scheduler, task):
        """This method is overwritten in Message subclasses.
        
        It should return True if the task should not be re-scheduled, any False-evaluating value otherwise.
        """
        
        raise NotImplementedError
