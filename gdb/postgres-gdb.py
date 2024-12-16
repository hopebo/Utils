#!/usr/bin/python
from __future__ import print_function # python2.X support

from utils.display import *
from utils.treewalker import TreeWalker
from utils.custom_regexp_pretty_printer \
    import CustomRegexpCollectionPrettyPrinter
import utils.convenience_variable as cv

# Define a postgres command prefix for all postgres related command
gdb.Command('pg', gdb.COMMAND_DATA, prefix=True)

def cast_void2node(val):
    try:
        nodetype = gdb.lookup_type('Node')
    except:
        return val

    return val.cast(nodetype.pointer())

def cast_node2real(val):
    node = val.dereference()
    typeStr = str(node['type'])

    # Some could haven't been initialized yet
    try:
        itsType = gdb.lookup_type(typeStr[2:]) # Strip prefix T_
    except:
        t_void = gdb.lookup_type("void")
        return t_void.pointer(), val.cast(t_void.pointer())

    return itsType.pointer(), val.cast(itsType.pointer())

'''
Node * printer
'''
class NodePrinter:
    "Print a pointer of Postgres base Node class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        castedVal = cast_node2real(self.val)[1]

        cv_name = cv.get_convenience_name()
        cv.gdb_set_convenience_variable(cv_name, castedVal)

        return cv.gdb_print_cv(cv_name, AdaptDisplay(castedVal))

'''
List * printer
'''
class PGListPrinter:
    class _iterator(object):
        def __init__(self, elements, typeStr, length):
            self.p = elements
            self.index = 0
            self.length = length
            self.convenience_name_prefix = cv.get_convenience_name()

            if typeStr == 'T_List':
                self.member_name = 'ptr_value'
            elif typeStr == 'T_IntList':
                self.member_name = 'int_value'
            elif typeStr == 'T_OidList':
                self.member_name = 'oid_value'
            else:
                self.member_name = 'xid_value'

            self.typeStr = typeStr

        def __iter__(self):
            return self

        def __next__(self):
            if self.index == self.length:
                raise StopIteration

            elt = self.p.dereference()[self.member_name]

            if self.typeStr == 'T_List':
                elt = cast_node2real(cast_void2node(elt))[1]

            cname = "%s%d" % (self.convenience_name_prefix, self.index)
            cv.gdb_set_convenience_variable(cname, elt)

            self.index = self.index + 1
            self.p = self.p + 1

            return ('$%s' % cname, '%s' % AdaptDisplay(elt))

        def next(self):
            """For python 2"""
            return self.__next__()

    def __init__(self, val):
        self.val = val
        if not self.val:
            return

        self.val = val.dereference()
        self.typeStr = str(self.val['type'])
        self.length = int(self.val['length'])
        self.allocated_length = int(self.val['max_length'])
        self.elements = self.val['elements']

    def children(self):
        if not self.val:
            return iter(())

        return self._iterator(self.elements, self.typeStr, self.length)

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        return "{} with {} elements, allocated length: {}".format(
            self.typeStr, self.length, self.allocated_length)

def build_pg_pretty_printer():
    pp = CustomRegexpCollectionPrettyPrinter(
        "postgres")
    pp.add_printer('Node *', '^(Node|Expr) \*[^*]*', NodePrinter)
    pp.add_printer('List *', '^List \*[^*]*', PGListPrinter)
    return pp

gdb.printing.register_pretty_printer(
    gdb.current_objfile(),
    build_pg_pretty_printer(),
    True)

class PGTreeWalker(TreeWalker):
    # Customized function to get data type of expression aligning PG codes
    def customized_cast_type(self, expr):
        return cast_node2real(cast_void2node(expr))

def traverse_pg_list(pg_list):
    children = []

    if not pg_list:
        return children

    pg_list = pg_list.dereference()
    length = int(pg_list['length'])

    if str(pg_list['type']) != 'T_List' or length == 0:
        return children

    p = pg_list['elements']
    for i in range(length):
        children.append(p.dereference()['ptr_value'])
        p = p + 1

    return children

'''
Postgres expression tree.
(gdb) pg exprtree Node/OpExpr/FuncExpr/BoolExpr,etc *
'''
class PGExpressionTraverser(gdb.Command, PGTreeWalker):
    """print postgres expression tree"""

    def __init__ (self):
        super(self.__class__, self).__init__(
            "pg exprtree", gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        if not arg:
            print("usage: pg exprtree [Node]")
            return
        expr = gdb.parse_and_eval(arg)
        self.walk(expr)

    #
    # walk functions for critical expression types
    #
    def walk_FuncExpr(self, val):
        return traverse_pg_list(val['args'])

    walk_OpExpr = walk_FuncExpr
    walk_BoolExpr = walk_FuncExpr

PGExpressionTraverser()
