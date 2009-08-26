# encoding: utf-8


__all__ = ['is_generator']


def is_generator(func):
    try:
        return hasattr(func, '__iter__') or ( func.func_code.co_flags & 0x20 != 0 )
    
    except AttributeError:
        return False
