#!/usr/bin/python
from __future__ import print_function # python2.X support
import re

from utils.display import *
from utils.treewalker import TreeWalker
from utils.custom_regexp_pretty_printer \
    import CustomRegexpCollectionPrettyPrinter
from utils.std_util import *
import utils.convenience_variable as cv

# Define a mysql command prefix for all mysql related command
gdb.Command('mysql', gdb.COMMAND_DATA, prefix=True)

'''
MySQL List<T> printing utility.
'''
def get_value_from_list_node(nodetype, node, conven_name):
    """Returns the value held in an list_node<_Val>"""

    val = node['info'].cast(nodetype.pointer())
    val = val.cast(val.dynamic_type)

    cv.gdb_set_convenience_variable(conven_name, val)

    return val

'''
GDB print List<T> command.
'''
class MySQLListPrinter:
    "Print a MySQL List"

    class _iterator(object):
        def __init__(self, nodetype, head):
            self.nodetype = nodetype
            self.base = head
            self.count = 0
            self.end_of_list = gdb.parse_and_eval('end_of_list').address
            self.convenience_name_prefix = cv.get_convenience_name()

        def __iter__(self):
            return self

        def __next__(self):
            if self.base == self.end_of_list:
                raise StopIteration
            elt = self.base.dereference()
            self.base = elt['next']
            count = self.count
            self.count = self.count + 1
            cname = "%s%d" % (self.convenience_name_prefix, count)
            val = get_value_from_list_node(self.nodetype, elt, cname)
            return ('$%s' % cname, '%s' % val)

        def next(self):
            """For python 2"""
            return self.__next__()

    def __init__(self, val):
        self.typename = val.type
        self.val = val

    def children(self):
        nodetype = self.typename.template_argument(0)
        return self._iterator(nodetype, self.val['first'])

    def to_string(self):
        return '%s' % self.typename if self.val['elements'] != 0 else 'empty %s' % self.typename

# (gdb) mysql qbtree SELECT_LEX_UNIT/SELECT_LEX
class QueryBlockTraverser(gdb.Command, TreeWalker):
    """print query block relationship"""

    def __init__ (self):
        super(self.__class__, self).__init__(
            "mysql qbtree", gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        if len(args) < 1:
            print("usage: mysql qbtree [SELECT_LEX_UNIT/SELECT_LEX]")
            return

        cur_select = gdb.parse_and_eval(args[0])

        master = cur_select
        while master:
            root = master
            master = root.dereference()['master']

        self.walk(root, cur_select)

    def walk_SELECT_LEX(self, select_lex):
        children = []
        unit = select_lex.dereference()['slave']
        while unit:
            children.append(unit)
            unit = unit.dereference()['next']

        return children

    walk_SELECT_LEX_UNIT = walk_SELECT_LEX

QueryBlockTraverser()

def traverse_mysql_list(item_list):
    end_of_list = gdb.parse_and_eval('end_of_list').address
    nodetype = item_list.type.template_argument(0)
    cur_elt = item_list['first']
    children = []
    while cur_elt != end_of_list:
        info = cur_elt.dereference()['info']
        children.append(info.cast(nodetype.pointer()))
        cur_elt = cur_elt.dereference()['next']
    return children

'''
MySQL Item expression tree.
'''
class ExpressionTraverser(gdb.Command, TreeWalker):
    """print mysql expression (Item) tree"""

    def __init__ (self):
        super(self.__class__, self).__init__(
            "mysql exprtree", gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        if not arg:
            print("usage: mysql exprtree [Item]")
            return
        expr = gdb.parse_and_eval(arg)
        self.walk(expr)

    #
    # walk functions for each Item class
    #
    def walk_Item_func(self, val):
        children = []
        for i in range(val['arg_count']):
            children.append(val['args'][i])
        return children

    walk_Item_sum = walk_Item_func

    def walk_Item_cond(self, val):
        return traverse_mysql_list(val['list'])

    def walk_Item_equal(self, val):
        children = traverse_mysql_list(val['fields'])
        if val['const_item']:
            children.append(val['const_item'])
        return children

ExpressionTraverser()

'''
MySQL Nested Join tree.
'''
class NestedJoinTraverser(gdb.Command, TreeWalker):
    """print mysql nested join tree"""

    def __init__ (self):
        super(self.__class__, self).__init__(
            "mysql nestedjoin", gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        if not arg:
            print("usage: mysql nestedjoin [TABLE_LIST]")
            return
        tl = gdb.parse_and_eval(arg)

        embedding = tl
        while embedding:
            root = embedding
            embedding = root.dereference()['embedding']

        self.walk(root, tl)

    def walk_TABLE_LIST(self, val):
        children = []

        if val['nested_join']:
            children = \
            traverse_mysql_list(val['nested_join'].dereference()['join_list'])

        return children

NestedJoinTraverser()

class ItemFieldPrinter:
    "Print a pointer to MySQL Item_field class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        item = self.val.dereference()
        trait = ""
        db_cata = []
        if item['table_name']:
            db_cata.append(item['table_name'].string())

        if item['field_name']:
            db_cata.append(item['field_name'].string())

        if len(db_cata) == 1:
            trait = db_cata[0]
        else:
            trait = "field = " + '.'.join(db_cata)

        return "{} {}".format(RawDisplay(self.val), trait)

class ItemDerivedPrinter:
    "Print a pointer to MySQL Item derived class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        val = self.val.cast(self.val.dynamic_type)
        return RawDisplay(val)

class BasePointerPrinter:
    "Print a pointer of MySQL base class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        # Case the base pointer to derived class.
        val_derived = self.val.cast(self.val.dynamic_type)
        return str(val_derived) if val_derived.type != self.val.type else \
            RawDisplay(self.val)

class TableListPrinter:
    "Print a pointer of MySQL TABLE_LIST class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        table_list = self.val.dereference()

        trait = ""
        if table_list['table_name'] and table_list['table_name'].string():
            trait = "table_name = " + table_list['table_name'].string()

        if table_list['nested_join']:
            trait += "nested join"

        if table_list['alias'] and table_list['alias'].string():
            trait += " as {}".format(table_list['alias'].string())

        if table_list['outer_join'] != 0:
            trait += " (outer)"
        else:
            trait += " (inner)"

        return "{} {}".format(RawDisplay(self.val), trait)

class MdlRequestPrinter:
    "Print a pointer of MySQL MDL_request class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        mdl_request = self.val.dereference()

        trait = "type = {}, duration = {}, key = {}".format(
            mdl_request['type'], mdl_request['duration'],
            mdl_request['key'].address)

        return "{} {}".format(RawDisplay(self.val), trait)

class MdlKeyPrinter:
    "Print a pointer of MySQL MDL_key class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        mdl_key = self.val.dereference()
        mdl_namespace = self.val['m_ptr'][0].cast(
            gdb.lookup_type('MDL_key::enum_mdl_namespace'))

        trait = "namespace = {}, m_ptr = {}".format(mdl_namespace,
                                                    mdl_key['m_ptr'])

        return "{} {}".format(RawDisplay(self.val), trait)

class FieldPrinter:
    "Print a pointer to MySQL Field class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        field = self.val.dereference()
        trait = ""
        db_cata = []
        if field['table_name'].dereference():
            db_cata.append(field['table_name'].dereference().string())

        if field['field_name']:
            db_cata.append(field['field_name'].string())

        trait = "field = " + '.'.join(db_cata)

        return "{} {}".format(RawDisplay(self.val), trait)

class SelArgPrinter:
    "Print a pointer of MySQL SEL_ARG class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        sel_arg = self.val.dereference()

        trait = "field = {}, min_value = {}, max_value = {}".format(
            sel_arg['field'], sel_arg['min_value'], sel_arg['max_value'])

        return "{} {}".format(RawDisplay(self.val), trait)

class SelectLexPrinter:
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return RawDisplay(self.val)

        tables = ""
        leaf_tables = self.val.dereference()['leaf_tables']
        has_tables = False
        while leaf_tables:
            has_tables = True
            lt = leaf_tables.dereference()
            tables += lt['table_name'].string() + ", "
            leaf_tables = lt['next_leaf']

        if has_tables:
            tables = "tables: " + tables[0 : len(tables) - 2]
        else:
            tables = "no tables"

        return "{} {}".format(RawDisplay(self.val), tables)

def build_mysql_pretty_printer():
    pp = CustomRegexpCollectionPrettyPrinter(
        "mysqld")
    pp.add_printer('List', '^List<.*>$', MySQLListPrinter)
    pp.add_printer('Item_field *', '^Item_field \*.*', ItemFieldPrinter)
    pp.add_printer('Item *', '^Item \*.*', BasePointerPrinter)
    pp.add_printer('Item_ *', '^Item_.* \*.*', ItemDerivedPrinter)
    pp.add_printer('PT *', '^PT.* \*.*', ItemDerivedPrinter)
    pp.add_printer('TABLE_LIST *', '^TABLE_LIST \*.*', TableListPrinter)
    pp.add_printer('MDL_request *', '^MDL_request \*.*', MdlRequestPrinter)
    pp.add_printer('MDL_key *', '^MDL_key \*.*', MdlKeyPrinter)
    pp.add_printer('Field *', '^Field \*.*', BasePointerPrinter)
    pp.add_printer('Field_ *', '^Field_.* \*.*', FieldPrinter)
    pp.add_printer('SEL_ARG *', '^SEL_ARG \*.*', SelArgPrinter)
    pp.add_printer('SELECT_LEX *', '^SELECT_LEX \*.*', SelectLexPrinter)
    return pp

gdb.printing.register_pretty_printer(
    gdb.current_objfile(),
    build_mysql_pretty_printer(),
    True)

'''
Helper function to determine whether the parameter is derived from
corresponding class.
'''
def derives_from(val, type_name):
    try:
        derived_type = gdb.lookup_type(type_name)
    except:
        return False

    try:
        derived = val.dynamic_cast(derived_type.pointer())
    except:
        return False

    return True if derived else False

class ItemStringPrinter:
    "Print a pointer to MySQL Item_string class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        item = self.val.dereference()
        trait = ""
        if item['str_value']['m_ptr']:
            trait = "{} \"{}\"".format("str_value =",
                                       item['str_value']['m_ptr'].string())

        return "{} {}".format(RawDisplay(self.val), trait)

class ItemIntPrinter:
    "Print a pointer to MySQL Item_int class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        val_derived = self.val.cast(self.val.dynamic_type)
        item = val_derived.dereference()
        trait = "value = " + str(item['value'])

        return "{} {}".format(RawDisplay(val_derived), trait)

class CustomPrettyPrinterLocator(gdb.printing.PrettyPrinter):
    """Given a gdb.Value, search for a custom pretty printer"""

    def __init__(self):
        super(CustomPrettyPrinterLocator, self).__init__(
            "misc", []
        )

    def __call__(self, val):
        """Return the custom formatter if the type can be handled"""

        typename = str(val.type)

        if derives_from(val, "Item_string"):
            return ItemStringPrinter(val)

        if derives_from(val, "Item_int"):
            return ItemIntPrinter(val)

        return None

gdb.printing.register_pretty_printer(
    gdb.current_objfile(),
    CustomPrettyPrinterLocator(),
    True)

"""
IMCI related pretty printers
"""
class ImciRelationTraverser(gdb.Command, TreeWalker):
    '''print IMCI relation tree'''

    def __init__(self):
        super(self.__class__, self).__init__(
            "mysql iqbtree", gdb.COMMAND_OBSCURE)
        self.meta = None

    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        if len(args) < 1:
            print("usage: mysql imcitree [RelationBase *] [MetadataCache *]")
            return

        cur_rel = gdb.parse_and_eval(args[0])
        # Passed in metadata provider to display more informations, which is
        # optional.
        if len(args) > 1:
            self.meta = gdb.parse_and_eval(args[1])

        parent = cur_rel
        while parent:
            root = parent
            parent = root.dereference()['parent_rel_']

        self.walk(root, cur_rel)

    def walk_Optimizer_RelationBase(self, relation):
        child_vec = relation.dereference()['child_rels_']
        children = traverse_std_vector(child_vec)

        return children

    def get_card_and_cost(self, rel):
        return "Card: {}, Cost: {}".format(rel.dereference()['card_']['card'],
                                           rel.dereference()['estimated_cost_'])

    def show_Optimizer_RelationBase(self, relation):
        return "{} {}".format(AdaptDisplay(relation),
                              self.get_card_and_cost(relation))

    def show_Optimizer_CTableScan(self, relation):
        table_name = ''

        if self.meta is not None:
            try:
                obj_map = self.meta.dereference()['object_map_']
                myiter = StdHashtableIterator(obj_map)

                for pair in myiter:
                    obj_id = pair['first']

                    if relation.dereference()['table_id_'] != obj_id:
                        continue

                    # Shared pointer
                    object_info = pair['second']
                    object_info = object_info['_M_ptr'].cast(
                        object_info.type.template_argument(0).pointer())

                    table_name = object_info.dereference()['name_']
            except:
                # Metainfo could have been expired for new query
                self.meta = None

        return "{} {} {}".format(AdaptDisplay(relation), table_name,
                                 self.get_card_and_cost(relation))

    show_Optimizer_TableScan = show_Optimizer_CTableScan

    def show_Optimizer_EqualJoin(self, relation):
        return "{} {} {}".format(AdaptDisplay(relation),
                                 relation.dereference()['join_type_'],
                                 self.get_card_and_cost(relation))

ImciRelationTraverser()

class ImciExpressionTraverser(gdb.Command, TreeWalker):
    '''print IMCI expression tree'''
    def __init__(self):
        super(self.__class__, self).__init__(
            "mysql iexprtree", gdb.COMMAND_OBSCURE)
        self.meta = None

    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        if len(args) < 1:
            print("usage: mysql iexprtree [Expression *] [MetadataCache *]")
            return

        expr = gdb.parse_and_eval(args[0])
        if len(args) > 1:
            self.meta = gdb.parse_and_eval(args[1])

        self.walk(expr)

    def walk_Optimizer_Expression(self, expr):
        child_vec = expr.dereference()['child_exprs_']
        # Traverse std::vector
        children = traverse_std_vector(child_vec)

        return children

    def show_Optimizer_Field(self, val):
        col_name = ''

        # Find table name from metacache
        if self.meta is not None:
            try:
                col_map = self.meta.dereference()['column_map_']
                myiter = RbtreeIterator(col_map)

                for pair in myiter:
                    tab_col_id = pair['first']

                    if val.dereference()['rel_id_'] != tab_col_id['table_id'] or \
                       val.dereference()['col_id_'] != tab_col_id['col_id']:
                        continue

                    # Shared pointer
                    column_info = pair['second']
                    column_info = column_info['_M_ptr'].cast(
                        column_info.type.template_argument(0).pointer())

                    col_name = column_info.dereference()['name_']
                    break
            except:
                # Metainfo could have been expired
                self.meta = None

        return "{} {}".format(AdaptDisplay(val), col_name)

    def show_Optimizer_Predicate(self, val):
        return "{} {}".format(AdaptDisplay(val),
                              val.dereference()['pred_type_'])

    def show_Optimizer_IntConst(self, val):
        return "{} {}".format(AdaptDisplay(val), val.dereference()['value_'])

    show_Optimizer_StrConst = show_Optimizer_IntConst
    show_Optimizer_DoubleConst = show_Optimizer_IntConst

ImciExpressionTraverser()
