#!/usr/bin/python

import gdb
import random

def get_convenience_name():
    return chr(ord('a') + random.randint(0, 25))

def gdb_set_convenience_variable(var_name, val):
    gdb.set_convenience_variable(var_name, val)
    return

def gdb_print_cv(cv_name, val):
    return "${} = {}".format(cv_name, val);
