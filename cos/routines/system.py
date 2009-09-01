# encoding: utf-8

from datetime                                   import timedelta

from cos.core                                   import Routine
from cos.constants                              import PRIORITY_NORMAL


__all__ = ['NoOp', 'GetTaskID', 'PauseTask', 'SleepTask', 'WakeTask', 'SpawnTask', 'KillTask']
log = __import__('logging').getLogger(__name__)


class NoOp(Routine):
    def handle(self, scheduler, task):
        pass


class GetTaskID(Routine):
    def handle(self, scheduler, task):
        task.messages.put(task.id)


class PauseTask(Routine):
    """Schedule the task to resume later through explicit resume."""

    def handle(self, scheduler, task):
        log.debug("Pausing task %r.", task)
        return True


class SleepTask(Routine):
    """Schedule the task to resume later; an interval after it was last scheduled or a specific datetime."""

    def __init__(self, queue=None, until=None, priority=PRIORITY_NORMAL, *args, **kw):
        self.queue = queue

        if queue is None:
            self.until = until if until else timedelta(*args, **kw)

        self.priority = priority

        super(SleepTask, self).__init__()

    def handle(self, scheduler, task):
        log.debug("Sleeping task.")

        if self.queue is not None:
            log.debug("Sleeping %r into queue.", task)
            self.queue.append(task.id)
            return True

        log.debug("Sleeping %r until %r.", task, self.until)
        scheduler.add(task, self.priority, when=self.until)
        return True


class WakeTask(Routine):
    def __init__(self, task, priority=PRIORITY_NORMAL):
        self.task = task
        self.priority = priority
    
    def handle(self, scheduler, task):
        scheduler.add(scheduler[self.task], self.priority)


class SpawnTask(Routine):
    def __init__(self, task, priority=PRIORITY_NORMAL):
        self.task = task
        self.priority = priority

    def handle(self, scheduler, task):
        scheduler.add(self.task, self.priority)


class KillTask(Routine):
    def __init__(self, task):
        self.task = task
    
    def handle(self, scheduler, task):
        scheduler.exit(scheduler[self.task])


class WaitBase(Routine):
    queue = 'core'
    kind = None
    
    def __init__(self, reference):
        self.reference = reference
    
    def handle(self, scheduler, task):
        if self.reference not in scheduler.queue.get(self.queue).get(self.kind):
            scheduler.queue.get(self.queue).get(self.kind)[self.reference] = []
        
        scheduler.queue.get(self.queue).get(self.kind)[self.reference].append(task.id)


class WaitForTask(WaitBase):
    kind = 'deathwatch'


class GetQueue(Routine):
    def __init__(self, queue, kind, reference=None):
        self.queue = queue
        self.kind = kind
        self.reference = reference
    
    def handle(self, scheduler, task):
        if not reference:
            task.messages.put(scheduler.queue.get(self.queue).get(self.kind))
            return
        
        task.messages.put(scheduler.queue.get(self.queue).get(self.kind).get(self.reference))
    