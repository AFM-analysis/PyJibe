import numpy as np


def equals(a, b):
    """Check if `a` equals `b` with support for arrays"""
    if a.__class__ != b.__class__:
        return False
    if isinstance(a, dict):
        if len(a) != len(b):
            return False
        ret = True
        for key in a:
            if key not in b:
                return False
            else:
                ret *= equals(a[key], b[key])
        return ret
    elif isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        ret = True
        for ii in range(len(a)):
            ret *= equals(a[ii], b[ii])
        return ret
    elif isinstance(a, np.ndarray):
        if len(a) != len(b):
            return False
        else:
            return np.all(a == b)
    else:
        return a == b
