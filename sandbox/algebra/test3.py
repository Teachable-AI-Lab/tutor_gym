
from numba.core.caching import Cache, _SourceFileBackedLocatorMixin, _CacheLocator, _UserProvidedCacheLocator, CompileResultCacheImpl
from numba.core.dispatcher import Dispatcher
from numba.core.serialize import dumps

from numba import njit
from numba import config
import os
import types as py_types
import functools
from copy import copy
import hashlib

import time
class PrintElapse():
    def __init__(self, name):
        self.name = name
    def __enter__(self):
        self.t0 = time.time_ns()/float(1e6)
    def __exit__(self,*args):
        self.t1 = time.time_ns()/float(1e6)
        print(f'{self.name}: {self.t1-self.t0:.6f} ms') 

class _PreciseCacheLocator(_UserProvidedCacheLocator):
    def __init__(self, py_func, py_file):
        self._py_func = py_func
        cache_subpath = self.get_suitable_cache_subpath(py_file)
        self._cache_path = os.path.join(config.CACHE_DIR, cache_subpath)

        with PrintElapse("hashing time"):
            code =  self._py_func.__code__
            glbs = self._py_func.__globals__

            # Get __globals__ referenced in the function body
            _vars = code.co_names
            used_globals = {k:glbs[k] for k in _vars if k in glbs}

            # Hash the function bytecode and subset of globals
            func_bytes = code.co_code + dumps(used_globals)
            self._func_hash = hashlib.sha256(func_bytes).hexdigest()
    
    def get_source_stamp(self):
        return self._func_hash

    def get_disambiguator(self):
        return self._func_hash[:10]

    @classmethod
    def from_function(cls, py_func, py_file):
        # if not config.CACHE_DIR:
        #     return
        self = cls(py_func, py_file)
        return self
        

class PreciseCacheImpl(CompileResultCacheImpl):
    _locator_classes = [
        _PreciseCacheLocator,
        *CompileResultCacheImpl._locator_classes
    ] 

class PreciseCache(Cache):
    """
    Implements Cache that saves and loads CompileResult objects.
    """
    _impl_class = PreciseCacheImpl


# Monkey Patch Dispatcher
def enable_caching(self):
    self._cache = PreciseCache(self.py_func)
Dispatcher.enable_caching = enable_caching

GLOBAL_VAL1 = 1
GLOBAL_VAL2 = 2
GLOBAL_VAL3 = 3

@njit(cache=True)
def foo():
    return GLOBAL_VAL1

@njit(cache=True)
def bar():
    return GLOBAL_VAL2

def gen_baz():
    x = GLOBAL_VAL3+0    
    @njit(cache=True)
    def baz():
        return x
    return baz

baz = gen_baz()
print(foo(), bar(), baz())
print("FOO", "HIT" if len(foo._cache_misses) == 0 else "MISS")
print("BAR", "HIT" if len(bar._cache_misses) == 0 else "MISS")
print("BAZ", "HIT" if len(baz._cache_misses) == 0 else "MISS")
