# encoding: utf-8

"""Coroutine constants."""


from decimal import Decimal


__all__ = ['PRIORITY_CRITICAL', 'PRIORITY_HIGH', 'PRIORITY_NORMAL', 'PRIORITY_LOW', 'PRIORITY_IDLE', 'PRIORITY_INCREMENT', 'Hz', 'KHz', 'MHz', 'GHz']



# Standard priority values.
PRIORITY_CRITICAL   = Decimal(" 1.0")
PRIORITY_HIGH       = Decimal(" 0.5")
PRIORITY_NORMAL     = Decimal(" 0.0")
PRIORITY_LOW        = Decimal("-0.5")
PRIORITY_IDLE       = Decimal("-1.0")

# Each time a task is re-scheduled add this to the priority.
# The priority for a task is reset when it sleeps.
PRIORITY_INCREMENT  = Decimal("0.001")


# Scheduling frequency constants.
Hz                  = 1.0
KHz                 = 1000 * Hz
MHz                 = 1000 * KHz
GHz                 = 1000 * MHz
