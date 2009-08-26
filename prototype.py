import sys, os
from time import sleep
from datetime import datetime as DateTime, timedelta as TimeDelta


# disable buffering
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)


def is_generator(func):
    try:
        return hasattr(func, '__iter__') or ( func.func_code.co_flags & 0x20 != 0 )
    
    except AttributeError:
        return False


class Event(object):
    def __init__(self, description=None, **kw):
        self.description, self.data = description, kw
    
    def __str__(self):
        if self.description:
            return "%s: %s" % (self.__class__.__name__, self.description)
        
        return self.__class__.__name__
    
    def __repr__(self):
        return "%s(\"%s\")" % (self.__class__.__name__, self.description if self.description else "")


class SpawnEvent(Event):
    pass

class ReadyEvent(Event):
    pass

class FinishedEvent(Event):
    pass

class NoOpEvent(Event):
    pass

class ContinueEvent(Event):
    def __init__(self, when, priority=0):
        self.when = when
        self.priority = priority
    
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.when)

class LogEvent(Event):
    pass

class SetOutputEvent(Event):
    def __init__(self, name, value):
        self.name, self.value = name, value
    
    def __repr__(self):
        return "%s = %r" % (self.name, self.value)



class Task(object):
    def __init__(self):
        self.queue = []
        self.process = None
    
    def __repr__(self):
        return "%s" % (self.__class__.__name__, )
    
    def __call__(self):
        self.startup()
        
        message = yield ReadyEvent("Task %s ready." % (id(self), ))
        
        try:
            while True:
                message = self.generator.send(message)
                
                if isinstance(message, FinishedEvent):
                    break
                
                if isinstance(message, Event):
                    message = yield message
            
        except StopIteration:
            pass
        
        self.shutdown()
        
        # If the task completed itself, return its event, otherwise we have to generate one of our own.
        if isinstance(message, FinishedEvent): yield message
        else: yield FinishedEvent("Task %s finished." % (id(self), ))
        
        # Explicitly raise a StopIteration exception.  Explicit is better than implicit.
        raise StopIteration
    
    def startup(self):
        if is_generator(self.execute):
            self.generator = self.execute()
        
        else:
            def generator():
                yield self.execute()
            
            self.generator = generator()
    
    def execute(self, message=None):
        raise NotImplementedError
    
    def shutdown(self):
        self.generator.close()


def make_task(func):
    class MyTask(Task):
        def __init__(self, *args, **kw):
            self.args, self.kw = args, kw
            super(MyTask, self).__init__()
        
        def execute(self):
            if not is_generator(func):
                yield func(*self.args, **self.kw)
                raise StopIteration
            
            generator = func(*self.args, **self.kw)
            
            while True:
                yield generator.next()
    
    return MyTask



class MultiplyReturn(Task):
    def __init__(self, a, b):
        self.a, self.b = a, b
        super(MultiplyReturn, self).__init__()
    
    def execute(self):
        return LogEvent("%d * %d = %d" % (self.a, self.b, self.a * self.b))


class MultiplyYield(Task):
    def __init__(self, a, b):
        self.a, self.b = a, b
        super(MultiplyYield, self).__init__()
    
    def execute(self):
        yield LogEvent("%d * %d = %d" % (self.a, self.b, self.a * self.b))


class MultiplyYieldSafe(Task):
    def __init__(self, a, b):
        self.a, self.b = a, b
        super(MultiplyYieldSafe, self).__init__()
    
    def execute(self):
        yield LogEvent("%d * %d = %d" % (self.a, self.b, self.a * self.b))
        yield FinishedEvent("Multiplication done.")


@make_task
def HelloWorld():
    yield LogEvent("Hello world!")

@make_task
def Divide(a, b):
    return LogEvent("%d / %d = %d" % (a, b, a / b))










class ScheduledExample(Task):
    def __repr__(self):
        return "ScheduledExample(%s)" % (self.delay)
    
    def __init__(self, time=5):
        if isinstance(time, int): self.delay = TimeDelta(seconds=time)
        elif isinstance(time, (DateTime, TimeDelta)): self.delay = time
        else: raise TypeError
        
        self.seconds = self.delay.seconds if isinstance(self.delay, TimeDelta) else (self.delay - DateTime.now()).seconds
        
        super(ScheduledExample, self).__init__()
    
    def execute(self):
        yield LogEvent("Waiting %d seconds." % (self.seconds, ))
        yield ContinueEvent(self.delay)
        yield LogEvent("Finished waiting %d seconds." % (self.seconds, ))


class DigitalOscillator(Task):
    def __repr__(self):
        return "%s(%f Hz)" % (self.__class__.__name__, self.hz)
    
    def __init__(self, frequency=None, initial_state=False, count=None):
        self.hz = frequency
        self.frequency = TimeDelta(seconds=1.0/frequency)
        self.state = initial_state # Output(initial_state)
        self.count = count
        
        super(Oscillator, self).__init__()

    def execute(self):
        message = None
        
        iteration = None
        if self.count is not None:
            iteration = 0
        
        while True:
            message = yield ContinueEvent(self.frequency) # Add this task to the time-sensitive queue.
            
            if isinstance(message, FinishedEvent):
                return
            
            while message is not None: # Ignore events we can't handle.
                yield None
            
            self.state = not self.state
            message = yield SetOutputEvent("state", self.state)
            
            iteration += 1
            if iteration == self.count:
                break
        
        yield FinishedEvent("Oscillator expired from natural causes.")


import math

sine = lambda x: math.sin(2.0 * math.pi * x)
square = lambda x: x - math.floor(x)



class Collection(list):
    def __init__(self, id, kind=None, *args, **kw):
        self.id = id
        self.kind = kind
        super(Collection, self).__init__(*args, **kw)


class IO(object):
    def __init__(self, id, state=None):
        self.id = id
        self.state = None

class Input(IO):
    pass

class Output(IO):
    pass


class Component(object):
    inputs = []
    outputs = []
    parts = []
    
    def __init__(self, id):
        self.id = id


class Constant(Component):
    inputs = [Input('value')]
    outputs = ['value']

high = Constant(value=True)
low = Constant(value=False)
impeded = Constant(value=None)



class Buffer(Component):
    inputs = [Input('value')]
    outputs = [Output('value')]
    
    def changed(self):
        self.value = self.value


class Inverter(Buffer):
    def changed(self):
        self.value = not self.value


class ControlledBuffer(Buffer):
    inputs = [Input('value'), Input('control')]
    
    def changed(self):
        self.value = self.value if self.control else None


class ControlledInverter(Buffer):
    inputs = [Input('value'), Input('control')]

    def changed(self):
        if self.value is None:
            self.value = None
        
        else:
            self.value = not self.value if self.control else None


class DigitalComponent(Component):
    inputs = [Collection('input', Input)]
    outputs = [Output('value')]


class OR(DigitalComponent):
    def changed(self):
        self.value = any(self.input.values())

class AND(DigitalComponent):
    def changed(self):
        if None in self.input.values():
            self.value = None
        else:
            self.value = all(self.input.values())

class XORReference(DigitalComponent):
    inputs = [Collection('input', Input, 2)]
    value = 'o.value'
    
    parts = [
            ANDComponent('a1', input=['self.input[1]', 'n1.value']),
            ANDComponent('a2', input=['self.input[1]', 'n2.value']),
            Inverter('n1', value='self.input[1]'),
            Inverter('n2', value='self.input[2]'),
            ORComponent('o', input=['a1.value', 'a2.value'])
        ]

class XOR(DigitalComponent):
    def changed(self):
        if None in self.input.values():
            self.value = None
        else:
            self.value = self.input.values().count(True) == 1

class Even(DigitalComponent):
    def changed(self):
        if None in self.input.values():
            self.value = None
        else:
            self.value = self.input.values().count(True) % 2 == 0

class Odd(DigitalComponent):
    def changed(self):
        if None in self.input.values():
            self.value = None
        else:
            self.value = self.input.values().count(True) % 2 == 1


class NAND(DigitalComponent):
    value = 'i.value'
    parts = [
            AND('a', input='self.input')
            Inverter('i', value='a.value')
        ]

class NOR(DigitalComponent):
    value = 'i.value'
    parts = [
            OR('a', input='self.input')
            Inverter('i', value='a.value')
        ]



class Multiplexer(DigitalComponent):
    inputs = [Collection('input', Input), Input('selection', Input)]
    
    def changed(self):
        if self.selection is Null:
            self.value = Null
        else:
            self.value = self.input[self.selection]

class Demultiplexer(DigitalComponent):
    inputs = [Input('input'), Input('selection', Input)]
    outputs = [Collection('value', Output)]

    def changed(self):
        if self.selection is Null:
            self.value = Null
        else:
            values = dict([(i, None) for i in self.value.keys()]
            values[self.selection] = self.input
            
            for i, j in values.iteritems():
                self.value[i] = j


class PriorityEncoder(Component):
    """The component has a number of inputs on its west edge, with the first labeled  0  and the other numbered from there. The component determines the indices of the inputs whose values are 1, and it emits the highest index. For example, if inputs 0, 2, 5, and 6 are all 1, then the priority encoder emits a value of 110. If no inputs are 1, or if the component is disabled, then the output of the priority encoder is floating.
    The priority encoder is designed so that a number of encoders can be daisy-chained to accommodate additional inputs. In particular, the component includes an enable input and an enable output. Whenever the enable input is 0, the component is disabled, and the output will be all floating bits. The enable output is 1 whenever the component is enabled and none of the indexed inputs are 1. Thus, you can take two priority encoders and connect the enable output of the first to the enable input of the second: If any of the indexed inputs to the first are 1, then the second will be disabled and so its output will be all floating. But if none of the first's indexed inputs are 1, then its output will be all-floating bits, and the second priority encoder will be enabled and it will identify the highest-priority input with a 1.
    An additional output of the priority encoder is 1 whenever the priority encoder is enabled and finds a 1 on one of the indexed inputs. When chaining priority encoders together, this output can be used to identify which of the encoders was triggered.
    """


class BitSelector(Component):
    """Given an input of several bits, this will divide it into several equal-sized groups (starting from the lowest-order bit) and output the group selected by the select input.
    For example, if we have an eight-bit input 01010101, and we are to have a three-bit output, then group 0 will be the lowest-order three bits 101, group 1 will be the next three bits, 010, and group 2 will be the next three bits 001. (Any bits beyond the top are filled in with 0.) The select input will be a two-bit number that selects which of these three groups to output; if the select input is 3, then 000 will be the output.
    """












#print "Testing a few things..."
#
#print "Process list for MultiplyReturn(2, 4): %r" % ([i for i in MultiplyReturn(2, 4)()], )
#print "Process list for MultiplyYield(4, 8): %r" % ([i for i in MultiplyYield(4, 8)()], )
# print "Process list for MultiplyYieldSafe(3, 6): %r" % ([i for i in MultiplyYieldSafe(3, 6)()], )
# print "Process list for HelloWorld(): %r" % ([i for i in HelloWorld()()], )
# print "Process list for Divide(64, 2): %r" % ([i for i in Divide(64, 2)()], )
# print "Process list for ScheduledExample(): %r" % ([i for i in ScheduledExample()()], )
# 
# print
# 
# print "Testing scheduler..."



class Scheduler(object):
    def __init__(self):
        self.tasks = []
        self.schedule = {}
    
    def add(self, task, priority=0):
        queue = []
        
        print " + Added task", repr(task)
        
        task.process = task()
        
        # Add the task to the stack of tasks currently available.
        self.tasks.append(task)
        
        # Schedule the task to be run immediately.
        self.schedule[(DateTime.now(), priority)] = task
    
    def get_schedule(self):
        schedule = self.schedule.keys()
        schedule.sort()
        
        now = DateTime.now() + TimeDelta(seconds=0.1) # add a little fudge-factor for slow sorting.
        next = None
        
        _schedule = []
        for time, priority in schedule:
            if time > now:
                next = (priority, time)
                break
            
            _schedule.append((priority, time))
        
        schedule = _schedule
        del _schedule
        
        schedule.sort()
        
        return schedule, next
    
    def run(self):
        print "Starting scheduler."
        
        while True:
            if not self.schedule or not self.tasks:
                print "Nothing left in the task queue or scheduler."
                break
            
            # Get a list of tasks that need to be run, sorted by priority.
            
            schedule, next = self.get_schedule()
            
            # The schedule is now limited to tasks that have to run, sorted by priority.  :)
            
            for priority, time in schedule:
                # Pop the task out of the schedule.
                task = self.schedule[(time, priority)]
                del self.schedule[(time, priority)]
                
                # Load next message, if any.
                if task.queue: message = task.queue.pop(0)
                else: message = None # NoOpEvent("No messages waiting.")
                
                # print " > Sent message", repr(message), "to task", repr(task)
                
                # Pass the message and accept one in return.
                message = task.process.send(message)
                
                # print " <", repr(task), '->', repr(message)
                
                if isinstance(message, NoOpEvent):
                    # print " / Task", repr(task), "removed from scheduler, but kept alive."
                    continue
                
                if isinstance(message, ContinueEvent):
                    # Re-schedule this task at a future time.
                    # If this is a TimeDelta, the time is relative to the time it was originally scheduled.
                    
                    when = time + message.when if isinstance(message.when, TimeDelta) else message.when
                    self.schedule[(when, message.priority)] = task
                    
                    # print " # Sleeping task", repr(task), "until", repr(when)
                    
                    continue
                
                if isinstance(message, FinishedEvent):
                    print " - Task", repr(task), "finished.\033[K"
                    
                    task.process.close()
                    self.tasks.remove(task)
                    del task
                    
                    continue
                
                # Re-schedule this task to run again at the same time.  It hasn't finished processing, but is returning control.
                # Very slightly increase the priority so long-running tasks get better service.
                
                print " !", repr(message), "\033[K"
                self.schedule[(time, priority + 0.05)] = task
            
            # Determine how long to sleep.
            
            schedule, next = self.get_schedule()
            
            schedule.append(next)
            if not schedule or not schedule[0]: continue
            
            now = DateTime.now()
            
            # print repr(schedule)
            if schedule[0][1] < now: continue
            
            delay = schedule[0][1] - now
            
            print " ~ Sleeping", repr(delay.seconds + (delay.microseconds / 1000000.0)), "seconds.\r", 
            
            sleep(delay.seconds + (delay.microseconds / 1000000.0))



scheduler = Scheduler()
scheduler.add(ScheduledExample(5))
scheduler.add(ScheduledExample(30))
scheduler.add(ScheduledExample(20))
scheduler.add(Digital(frequency=1.0/4, count=7)) # 7 times, once every 4 seconds.
# scheduler.add(Oscillator(frequency=KHz, count=4 * KHz)) # This works!
scheduler.run()