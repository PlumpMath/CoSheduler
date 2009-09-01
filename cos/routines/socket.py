# encoding: utf-8

from cos.core                                   import Routine
from cos.routines.system                        import WaitBase
from cos.constants                              import PRIORITY_NORMAL


__all__ = ['FileReadWait', 'FileWriteWait']




class FileReadWait(Routine):
    """Schedule the task to resume once a file handle becomes readable."""
    
    queue = 'io'
    kind = 'read'


class FileWriteWait(Routine):
    """Schedule the task to resume once a file handle becomes writable."""
    
    queue = 'io'
    kind = 'write'
