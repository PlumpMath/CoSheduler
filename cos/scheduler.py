# encoding: utf-8

from time import sleep
from datetime import datetime, timedelta



log = __import__('logging').getLogger(__name__)
__all__ = ['Scheduler']



class Scheduler(object):
    running = False
    
    def __init__(self):
        self.queue
        
        self.tasks = []
        self.schedule = {}
    
    def add(self, task, priority=0):
        queue = []
        
        print " + Added task", repr(task)
        
        task.process = task()
        
        # Add the task to the stack of tasks currently available.
        self.tasks.append(task)
        
        # Schedule the task to be run immediately.
        # It is up to the task to schedule itself in the future.
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

