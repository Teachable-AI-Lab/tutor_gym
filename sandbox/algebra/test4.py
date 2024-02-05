import dis

def foo():
    pass

print(dis.Bytecode(foo, show_caches=True).info())

def foo():
    pass

print(dis.Bytecode(foo, current_offset=True).info())

