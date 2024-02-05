import types as py_types
import inspect
import functools
from copy import copy


def copy_func_w_new_globals(f, glbls, module=None):
    g = py_types.FunctionType(f.__code__, glbls, name=f.__name__, argdefs=f.__defaults__, closure=f.__closure__)
    g = functools.update_wrapper(g, f)
    g.__module__ = None
    g.__kwdefaults__ = copy(f.__kwdefaults__)
    return g

def create_function(f):
    code = f.__code__
    print(code.co_argcount,
                                code.co_kwonlyargcount,
                                code.co_nlocals,
                                code.co_stacksize,
                                code.co_flags,
                                code.co_code,
                                code.co_consts,
                                code.co_names,
                                code.co_varnames,
                                code.co_freevars,
                                code.co_cellvars,
                                code.co_filename,
                                code.co_name,
                                # code.co_qualname,
                                code.co_firstlineno,
                                code.co_lnotab,
                                # code.co_linetable,
                                # code.co_exceptiontable,
                                 
                                )
    args = []
    for attr, val in inspect.getmembers(code):
        if(attr == 'co_filename'):
            args.append("footbol")
        elif "co_" in attr:
            args.append(val)

    code = copy(code)
    code.co_filename = "poop"
    # y_code = py_types.CodeType(code.co_argcount,
    #                             code.co_kwonlyargcount,
    #                             code.co_nlocals,
    #                             code.co_stacksize,
    #                             code.co_flags,
    #                             code.co_code,
    #                             code.co_consts,
    #                             code.co_names,
    #                             code.co_varnames,
    #                             code.co_freevars,
    #                             code.co_cellvars,
    #                             code.co_filename,
    #                             code.co_name,
    #                             # code.co_qualname,
    #                             code.co_firstlineno,
    #                             code.co_lnotab,
    #                             # code.co_linetable,
    #                             # code.co_exceptiontable,
                                 
    #                             )

    return py_types.FunctionType(code, y.func_globals, name)


def foo():
    return 0

goo = create_function(foo)

# goo = copy_func_w_new_globals(foo, {})

print(inspect.getfile(foo))
print(inspect.getfile(goo))
