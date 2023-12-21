#!/usr/bin/python

import gdb
import random
import traceback

rotate = 0
def get_convenience_name():
    global rotate
    cur = rotate
    rotate = (rotate + 1) % 26
    # traceback.print_stack()
    return chr(ord('a') + cur)

def gdb_set_convenience_variable(var_name, val):
    gdb.set_convenience_variable(var_name, val)
    return

def gdb_print_cv(cv_name, val):
    return "${} = {}".format(cv_name, val);
