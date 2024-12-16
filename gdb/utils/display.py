import gdb

'''
Print object in raw format without pretty-printer
'''
def RawDisplay(value):
    if hasattr(gdb.Value, 'format_string'):
        info = value.format_string(raw = True)
    else:
        if value.dynamic_type.code == gdb.TYPE_CODE_PTR:
            # Cast pointer type to void * to avoid pretty printer
            t_void = gdb.lookup_type("void")
            info = str(value.cast(t_void.pointer()))
        else:
            info = str(value)

    return "({}) {}".format(value.dynamic_type, info)

'''
Print object with optional pretty-printer
'''
def AdaptDisplay(value):
    # Cast python boolean/integer/string to gdb.Value
    if not isinstance(value, gdb.Value):
        value = gdb.Value(value)

    # If pretty printer exists for the type, use the printer. Otherwise, print
    # in raw format.
    if gdb.default_visualizer(value) is not None:
        # Compatible with lower version gdb
        if hasattr(gdb.Value, 'format_string'):
            return value.format_string()
        else:
            return str(value)
    else:
        return RawDisplay(value)
