import functools
import hashlib
import pathlib
import warnings

import numpy as np


def hashfile(fname, blocksize=65536, count=0, constructor=hashlib.md5,
             hasher_class=None):
    """Compute md5 hex-hash of a file

    Parameters
    ----------
    fname: str or pathlib.Path
        path to the file
    blocksize: int
        block size in bytes read from the file
        (set to `0` to hash the entire file)
    count: int
        number of blocks read from the file
    hasher_class: callable
        deprecated, see use `constructor` instead
    constructor: callable
        hash algorithm constructor
    """
    if hasher_class is not None:
        warnings.warn("The `hasher_class` argument is deprecated, please use "
                      "`constructor` instead.")
        constructor = hasher_class
    path = pathlib.Path(fname).resolve()
    return _hashfile_cached(
        path=path,
        stat=path.stat(),
        blocksize=blocksize,
        count=count,
        constructor=constructor
    )


@functools.lru_cache(maxsize=100)
def _hashfile_cached(path, stat, blocksize=65536, count=0,
                     constructor=hashlib.md5):
    """Cached hashfile using stat tuple as cache

    This is a privat function. Please use `hashfile` instead!

    Parameters
    ----------
    path: pathlib.Path
        path to the file to be hashed
    stat: named tuple
        tuple of `os.stat_result` for `path`. This must be specified,
        so that caching of the result is done properly in case the user
        modified `path` (this function is wrapped with
        functools.lru_cache)
    blocksize: int
        block size in bytes read from the file
        (set to `0` to hash the entire file)
    count: int
        number of blocks read from the file
    constructor: callable
        hash algorithm constructor
    """
    assert stat, "We need stat for validating the cache"
    hasher = constructor()
    with path.open('rb') as fd:
        buf = fd.read(blocksize)
        ii = 0
        while len(buf) > 0:
            hasher.update(buf)
            buf = fd.read(blocksize)
            ii += 1
            if count and ii == count:
                break
    return hasher.hexdigest()


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
