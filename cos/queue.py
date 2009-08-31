# encoding: utf-8

import                                          collections

from cos.routines.system                        import NoOp, GetTaskID, PauseTask, WakeTask


__all__ = ['Queue', 'AsyncQueue']
log = __import__('logging').getLogger(__name__)



class Queue(object):
    """A multi-producer, multi-consumer FIFO queue.
    
    Can be used for exchanging data between tasks.
    """
    
    def __init__(self, iterable=(), maxlen=None):
        self.maxlen = maxlen
        self.queue = collections.deque(iterable, maxlen)
    
    def get(self):
        'Get the next item off the queue.'
        
        return self.queue.popleft()
    
    def put(self, item):
        'Append an item to the queue.'
        
        self.queue.append(item)
    
    @property
    def empty(self):
        'Return True is the queue is empty, False otherwise.'
        
        return (len(self.queue) == 0)
    
    @property
    def full(self):
        'Return True is the queue is full, False otherwise.'
        
        return ( len(self.queue) >= self.maxlen ) if self.maxlen is not None else False


class AsyncQueue(Queue):
    def __init__(self, iterable=(), maxlen=None):
        self.waiting = []
        super(AsyncQueue, self).__init__()
    
    def get(self):
        if self.empty:
            log.debug("Waiting for value to be added to the queue %r.", id(self))
            
            task = yield GetTaskID()
            self.waiting.append(task)
            
            log.debug("Pausing task.")
            yield PauseTask()
        
        yield self.queue.popleft()
    
    def put(self, item):
        log.debug("Adding %r to queue %r.", item, id(self))
        self.queue.append(item)
        log.debug("Queue %r is now %r.", id(self), self.queue)
        
        if self.waiting:
            log.debug("Put a value, broadcasting to item 0 of %r.", self.waiting)
            yield WakeTask(self.waiting.pop(0))
        
        yield NoOp()
