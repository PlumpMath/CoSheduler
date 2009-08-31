# encoding: utf-8

from cos.core                                   import Routine
from cos.constants                              import PRIORITY_NORMAL


__all__ = ['FileReadWait', 'FileWriteWait']




class FileReadWait(Routine):
    """Schedule the task to resume once a file handle becomes readable."""
    
    def handle(self, scheduler, task):
        log.debug("Pausing task %r.", task)
        return True


class FileWriteWait(Routine):
    """Schedule the task to resume once a file handle becomes writable."""
    
    def handle(self, scheduler, task):
        log.debug("Pausing task %r.", task)
        return True
