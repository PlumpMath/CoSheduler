# encoding: utf-8

import                                          types

from time                                       import sleep
from datetime                                   import datetime, timedelta
from decimal                                    import Decimal

from cos.constants                              import PRIORITY_NORMAL, PRIORITY_INCREMENT
from cos.core                                   import Tasklet, Task, Routine
from cos.utils                                  import adict
from cos.queue                                  import Queue

from cos.routines.system                        import NoOp



log = __import__('logging').getLogger(__name__)
__all__ = ['Scheduler']



class SchedulingConflict(Exception):
    """Unwilling to double-book the given task."""
    pass



class Scheduler(dict):
    """Coroutine scheduler.
    
    @type running: boolean
    @ivar running: Is the scheduler active and processing tasks?
    
    @type paused: boolean
    @ivar paused: Has the scheduler exhausted active tasks?
    
    @type delays: L{Queue<Queue>}
    @ivar delays: A circular list containing the amount of time each cycle has taken to process.  Used to perform readahead.
    
    @type queue: L{adict<adict>}
    @ivar queue: A dynamic collection of queues which tasks can be suspended to.  Used by queue runners to allow tasks to be suspended pending input, etc.  E.g. core.schedule, core.idle, io.read, io.write, io.ready, etc.
    """
    
    def __init__(self):
        self.running = False
        self.paused = False
        self.delays = Queue(maxlen=10)
        
        self.queue = dict()
        self.queue['core'] = dict()
        self.queue['core']['schedule'] = dict()
        self.queue['core']['deathwatch'] = dict()
        self.queue['core']['idle'] = []
    
    def add(self, task, priority=PRIORITY_NORMAL, parent=None, when=None):
        """Add a task to the scheduler.
        
        @type  task: generator, callable, Task, Tasklet
        @param task: Any callable, or an existing Task instance.
        
        @type  priority: Decimal
        @param priority: The priority of the given task, ranging from -1.0 (lowest) to 1.0 (highest).
        
        @type  parent: Task
        @param parent: The parent task, if the task being added is a subroutine.
        
        @type  when: datetime, timedelta
        @param when: The specific or relative time to execute this task.
        
        @rtype: L{UUID<uuid.UUID>}
        @return: The UUID unique ID of the task.
        """
        
        # Process the input task and, in the end, store a Tasklet instance.
        
        if not isinstance(priority, Decimal): raise TypeError
        
        if not isinstance(task, (Tasklet, Task, types.GeneratorType)) and not callable(task):
            raise TypeError
        
        if not isinstance(task, Tasklet):
            log.debug('%r is not a Tasklet', task)
            
            if not isinstance(task, types.GeneratorType):
                log.debug('%r is not a generator yet', task)
                task = task()
            
            task = Tasklet(task, priority, parent)
        
        elif task.id in self.queue['core']['schedule'].itervalues():
            raise SchedulingConflict()
        
        if task.id not in self:
            log.debug('%r is not present in the system', task)
            self[task.id] = task
        
        # Process the time and schedule the task to run.
        
        if when is None: when = datetime.now()
        elif isinstance(when, timedelta): when = datetime.now() + when
        
        log.debug("Scheduling %r for %r.", task, (when, priority))
        self.queue['core']['schedule'][(when, priority)] = task.id
        log.debug("Schedule: %r", self.queue['core']['schedule'])
        
        return task.id
    
    def exit(self, task):
        log.debug("Task %s is exiting.", task.id)
        del self[task.id]
        
        for i in self.queue['core']['deathwatch'].pop(task.id, []):
            self.add(self[i], self[i].priority)
    
    def schedule(self, remove=True):
        """Return the current time, a list of tasks to run, and the first task of the next iteration."""
        
        log.debug("queue=%r", self.queue)
        log.debug("Loading schedule: %r", self.queue['core']['schedule'])
        
        def _sort(a, b):
            """Key sort when preparing the schedule for a single iteration."""
            
            if a[1] == b[1]:
                return cmp(a[0], b[0])
            
            return cmp(a[1], b[1])
        
        # Get the current time and adjust for the average iteration processing time.
        now = datetime.now()
        now_ = now + ( timedelta() if self.delays.empty else ( sum(self.delays.queue, timedelta()) / len(self.delays.queue) ) )
        
        log.debug('Latency average: %r', 0 if self.delays.empty else sum(self.delays.queue, timedelta()) / len(self.delays.queue))
        
        # Sort by scheduled time.
        _, next = self.queue['core']['schedule'].keys(), None
        _.sort()
        
        # Limit to items before now and trap the next iteration's first task.
        schedule = []
        for i in _:
            if i[0] > now_:
                next = (i[0], i[1], self.queue['core']['schedule'][i])
                break
            
            schedule.append((i[0], i[1], self.queue['core']['schedule'][i]))
            if remove: del self.queue['core']['schedule'][i]
        
        del _
        
        # Sort by priority, then time.
        schedule.sort(_sort)
        
        log.debug("%d tasks, %d pending, %d selected for execution.", len(self), len(self.queue['core']['schedule']), len(schedule))
        
        return now, schedule, next
    
    def execute(self, task, priority=PRIORITY_NORMAL, scheduled=None):
        log.debug("Preparing to call %r.", task)
        
        message = None if task.messages.empty else task.messages.get()
        
        try:
            if isinstance(message, Exception): message = task.throw(message)
            else: message = task.send(message)
            log.debug("Received %r from %r.", message, task)
        
        except StopIteration, e:
            if task.parent:
                # Re-schedule the parent task to execute right now with a slightly higher priority.
                if e.args: task.parent.messages.put(e.args[0])
                self.add(task.parent, task.parent.priority + PRIORITY_INCREMENT)
            
            self.exit(task)
            return
        
        except Exception, e:
            del self[task.id]
            
            # Pass exceptions to the caller, if any, otherwise die.
            if task.parent:
                task.parent.messages.put(e)
                return
            
            log.exception("Error.")
            raise
        
        if isinstance(message, types.GeneratorType):
            # Suspend this task and schedule the subroutine.
            log.debug("Received a generator, adding child task %r.", message)
            self.add(message, parent=task)
            return
        
        if isinstance(message, Routine):
            if message.handle(self, task): return
        
        if task.parent and not isinstance(message, Routine):
            # Pass messages on to the caller.
            log.debug("Passing message %r to %r.", message, task.parent)
            task.parent.messages.put(message)
        
        # Re-schedule the task to run again, right now, with a slightly higher priority.
        self.add(task, priority + PRIORITY_INCREMENT)
    
    def run(self):
        self.running = True
        self.paused = False
        
        log.info("Starting scheduler.")
        
        while True:
            # Pause (kill our thread) if there are no tasks.
            if not len(self.queue['core']['schedule']):
                log.info("Nothing remaining in the process list.  Pausing.")
                self.running = False
                self.paused = True
                return
            
            # Get a list of tasks that need to be run, sorted by priority.
            now, schedule, next = self.schedule()
            log.debug("now, schedule, next = %r, %r, %r", now, schedule, next)
            
            # Loop through all tasks slated for the current iteration.
            # Tasks have already been removed from the scheduler at this point.
            for scheduled, priority, task in schedule:
                task = self[task]
                log.debug("Running %r", task)
                self.execute(task, priority, scheduled)
            
            # Add the current processing time to the list of delays.
            self.delays.put(datetime.now() - now)
            
            # Now that we've completed one iteration, examine the next task and sleep until it wakes.
            now, schedule, next = self.schedule(False)
            log.debug("now, schedule, next = %r, %r, %r", now, schedule, next)
            schedule.append(next)
            
            next = [i for i in schedule if i]
            if next: next = next[0]
            
            log.debug("%r", (next[0] < now) if next else None)
            
            # If we've run into the time for the next task, loop immediately.
            if ( not next ) or next[0] < now: continue
            
            # Perform idle tasks.
            
            for task in self.queue['core']['idle']:
                task = self[task]
                self.execute(task, task.priority)
            
            _ = next[0] - now
            log.debug("now=%r", now)
            log.debug("next=%r", next)
            log.debug("next[0]=%r", next[0])
            log.debug("_=%r", _)
            log.debug("Sleeping for %r.", _.seconds + (_.microseconds / 1000000.0))
            sleep(_.seconds + (_.microseconds / 1000000.0))
            del _


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(lineno)d -- %(message)s")
    
    from cos.queue import AsyncQueue
    from cos.routines.system import GetTaskID, SleepTask, PauseTask, WakeTask
    
    a = Scheduler()
    
    def printer(name):
        for i in xrange(1, 4):
            log.info('%s: %d', name, i)
            yield
    
    a.add(printer('foo'))
    a.add(printer('bar'))
    a.add(printer('baz'))
    
    a.run()
    
    def producer(foo="Foo"):
        yield foo
    
    def consume(producer, *args, **kw):
        log.info("Consumer preparing.")
        yield
        a = yield producer(*args, **kw)
        log.info("Consumer received %r.", a)
        yield
        log.info("Consumer finished.")
    
    a.add(consume(producer))
    a.add(consume(producer, "Bar"))
    a.add(consume(producer, foo="Baz"))
    
    a.run()
    
    def sleeper():
        log.info("Sleeping 2 seconds...")
        yield SleepTask(seconds=2)
        log.info("Done sleeping.")
    
    a.add(sleeper())
    
    a.run()
    
    print
    
    def myid():
        this = yield GetTaskID()
        log.info("My ID is: %r", this)
    
    a.add(myid())
    a.run()
    
    
    print
    
    tasks = []
    
    def myid(tasks):
        this = yield GetTaskID()
        log.info("My ID is: %r", this)
        
        tasks.append(this)
        log.info("Suspending permanantly.")
        yield PauseTask()
        
        log.warn("Was restarted!")
    
    def unpause(tasks):
        log.info("Waiting 5 seconds to resume task.")
        yield SleepTask(seconds=5)
        
        for i in tasks:
            log.info("Waking %r", i)
            yield WakeTask(i)
            log.info("Woke task.")
    
    a.add(myid(tasks))
    a.add(unpause(tasks))
    
    a.run()
    
    print
    
    queue = AsyncQueue()
    
    def producer(queue):
        log.info("Producer: starting")
        
        yield queue.put(1)
        
        log.info("Producer: sleeping")
        
        yield SleepTask(seconds=2)
        yield queue.put(2)
        
        log.info("Producer: finished")
    
    def consumer(queue):
        log.info("Consumer: starting")
        
        i = yield queue.get()
        log.info("Consumer: received %r", i)
        
        i = yield queue.get()
        log.info("Consumer: received %r", i)
        
        log.info("Consumer: finished")
    
    a.add(producer(queue))
    a.add(consumer(queue))
    
    a.run()
    
    
    print
    
    queue = AsyncQueue()
    
    def producer(queue):
        log.info("Producer Starting.")
        
        yield SleepTask(seconds=0.5)
        
        for i in range(4):
            yield SleepTask(seconds=0.5)
            
            log.info("Injecting %d into queue.", i)
            yield queue.put(i)
        
        log.info("Producer Finished.")
    
    def consumer(queue):
        log.info("Consumer Starting.")
        
        for i in range(4):
            log.info("Requesting value from queue.")
            a = yield queue.get()
            log.info("Received %d from queue.", a)
        
        log.info("Consumer finished.")
    
    a.add(producer(queue), priority=Decimal('0.5'))
    a.add(consumer(queue), priority=Decimal('-0.5'))
    
    a.run()
    
    
    print