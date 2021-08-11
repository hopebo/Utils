#!/usr/bin/python
from __future__ import print_function # python2.X support
import re

import utils.convenience_variable as cv

# Define a mysql command prefix for all mysql related command
gdb.Command('mysql', gdb.COMMAND_DATA, prefix=True)

'''
Thread printing utility.
'''
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def gdb_threads():
    if hasattr(gdb, 'selected_inferior'):
        threads = gdb.selected_inferior().threads()
    else:
        threads = gdb.inferiors()[0].threads()
    return threads

def pretty_frame_name(frame_name):
    """omit some stdc++ stacks"""
    pretty_names = (
        ('std::__invoke_impl', ''),
        ('std::__invoke', ''),
        ('std::_Bind', ''),
        ('Runnable::operator()', ''),
        ('std::thread::_Invoker', ''),
        ('std::thread::_State_impl', 'std::thread'),
        ('std::this_thread::sleep_for', 'std..sleep_for'))

    for templ, val in pretty_names:
        if frame_name.startswith(templ):
            return val

    return frame_name

def brief_backtrace(filter_threads):
    frames = ''
    frame = gdb.newest_frame() if hasattr(gdb, 'newest_frame') else gdb.selected_frame()
    while frame is not None:
        frame_name = frame.name() if frame.name() is not None else '??'
        if filter_threads is not None and frame_name in filter_threads:
            return None
        frame_name = pretty_frame_name(frame_name)
        if frame_name:
            frames += frame_name + ','
        frame = frame.older()
    frames = frames[:-1]
    return frames

'''
GDB thread search command.
'''
class ThreadSearch(gdb.Command):
    """find threads given a regex which matchs thread name, parameter name or value"""

    def __init__ (self):
        super (ThreadSearch, self).__init__ ("thread search", gdb.COMMAND_OBSCURE)

    def invoke (self, arg, from_tty):
        pattern = re.compile(arg)
        threads = gdb_threads()
        old_thread = gdb.selected_thread()
        for thr in threads:
            thr.switch()
            backtrace = gdb.execute('bt', False, True)
            matched_frames = [fr for fr in backtrace.split('\n') if pattern.search(fr) is not None]
            if matched_frames:
                print(thr.num, brief_backtrace(None))

        old_thread.switch()

ThreadSearch()

'''
GDB thread overview command.
'''
class ThreadOverview(gdb.Command):
    """print threads overview, display all frames in one line and function name only for each frame"""
    # filter Innodb backgroud workers
    filter_threads = (
        # Innodb backgroud threads
        'log_closer',
        'buf_flush_page_coordinator_thread',
        'log_writer',
        'log_flusher',
        'log_write_notifier',
        'log_flush_notifier',
        'log_checkpointer',
        'lock_wait_timeout_thread',
        'srv_error_monitor_thread',
        'srv_monitor_thread',
        'buf_resize_thread',
        'buf_dump_thread',
        'dict_stats_thread',
        'fts_optimize_thread',
        'srv_purge_coordinator_thread',
        'srv_worker_thread',
        'srv_master_thread',
        'io_handler_thread',
        'event_scheduler_thread',
        'compress_gtid_table',
        'ngs::Scheduler_dynamic::worker_proxy'
        )
    def __init__ (self):
        super (ThreadOverview, self).__init__ ("thread overview", gdb.COMMAND_OBSCURE)

    def invoke (self, arg, from_tty):
        threads = gdb_threads()
        old_thread = gdb.selected_thread()
        thr_dict = {}
        for thr in threads:
            thr.switch()
            bframes = brief_backtrace(self.filter_threads)
            if bframes is None:
                continue
            if bframes in thr_dict:
                thr_dict[bframes].append(thr.num)
            else:
                thr_dict[bframes] = [thr.num,]
        thr_ow = [(v,k) for k,v in thr_dict.items()]
        thr_ow.sort(key = lambda l:len(l[0]), reverse=True)
        for nums_thr,funcs in thr_ow:
           print (bcolors.FAIL, ','.join([str(i) for i in nums_thr]),bcolors.ENDC, funcs)
        old_thread.switch()

ThreadOverview()

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

from gdb.printing import RegexpCollectionPrettyPrinter
# Make pointer of dynamic types supported.
class CustomRegexpCollectionPrettyPrinter(RegexpCollectionPrettyPrinter):
    def __init__(self, name):
        super(CustomRegexpCollectionPrettyPrinter, self).__init__(name)

    def __call__(self, val):
        # Compatible for pointer of dynamic types.
        typename = str(val.type)
        if not typename:
            return None

         # Iterate over table of type regexps to determine
         # if a printer is registered for that type.
         # Return an instantiation of the printer if found.
        for printer in self.subprinters:
            if printer.enabled and printer.compiled_re.search(typename):
                return printer.gen_printer(val)

        # Cannot find a pretty printer.  Return None.
        return None

'''
MySQL query block structure.
'''
class MySQLQueryBlock(object):
    def __init__(self, stack_depth, index, value):
        self.stack_depth = stack_depth
        self.index = index
        self.value = value

    def __str__(self):
        if self.stack_depth == 0:
            prefix = ''
        else:
            prefix = ' ' * 3 * (self.stack_depth - 1) + '|--'

        tables = ""
        if self.value.dynamic_type.target().name == "SELECT_LEX":
            leaf_tables = self.value.dereference()['leaf_tables']
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

        return "{}{} ({}) {} {}".format(prefix, str(self.index),
                                        self.value.dynamic_type, self.value, tables)

'''
GDB qbtree print query block tree command.
'''
try:
    import Queue
except:
    import queue as Queue
# (gdb) mysql qbtree SELECT_LEX_UNIT/SELECT_LEX
class QueryBlockTree(gdb.Command):
    """print query block relationship"""
    def __init__ (self):
        super(self.__class__, self).__init__ ("mysql qbtree", gdb.COMMAND_OBSCURE)

    def add_object(self, queue, select, stack_depth):
        index = 0
        while select:
            queue.put(MySQLQueryBlock(stack_depth, index, select))
            slave = select.dereference()['slave']
            if slave:
                self.add_object(queue, slave, stack_depth + 1)
            select = select.dereference()['next']
            index += 1

    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        if len(args) < 1:
            print("usage: mysql qbtree [SELECT_LEX_UNIT/SELECT_LEX]")
            return

        q = Queue.Queue()
        select = args[0]
        select = gdb.parse_and_eval(select)
        master = select.dereference()['master']
        while master:
            select = master
            master = select.dereference()['master']

        self.add_object(q, select, 0)

        cv_name_prefix = cv.get_convenience_name()
        i = 0
        while not q.empty():
            element = q.get()
            cv_name = "%s%d" % (cv_name_prefix, i)
            print("${} = {}".format(cv_name, element))
            cv.gdb_set_convenience_variable(
                cv_name, element.value.cast(element.value.dynamic_type))
            i += 1

QueryBlockTree()

'''
MySQL Item expression tree.
'''
class ExpressionTraverser(gdb.Command):
    """print mysql expression (Item) tree"""

    def __init__ (self):
        super(self.__class__, self).__init__ ("mysql exprtree", gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        if not arg:
            print("usage: mysql exprtree [Item]")
            return
        expr = gdb.parse_and_eval(arg)
        self.cname_prefix = cv.get_convenience_name()
        self.var_index = 0
        self.level_graph = []
        self.do_walk(expr, 0)

    def do_walk(self, expr, level):
        expr_typed = expr.dynamic_type
        expr_casted = expr.cast(expr_typed)
        level_graph = '  '.join(self.level_graph[:level])
        for i, c in enumerate(self.level_graph):
            if c == '`':
                self.level_graph[i] = ' '
        cname = "%s%d" % (self.cname_prefix, self.var_index)
        left_margin = "{}${} =".format('' if level == 0 else '--', cname)
        self.var_index += 1
        item_show_info = ''
        print("{}{} {}".format(level_graph, left_margin, expr))
        cv.gdb_set_convenience_variable(cname, expr_casted)
        walk_func = self.get_walk_func(expr_typed.target())
        if walk_func is None:
            return
        children = walk_func(expr_casted)
        if not children:
            return
        if len(self.level_graph) < level + 1:
            self.level_graph.append('|')
        else:
            self.level_graph[level] = '|'
        for i, child in enumerate(children):
            if i == len(children) - 1:
                self.level_graph[level] = '`'
            self.do_walk(child, level + 1)

    def get_action_func(self, item_type, action_prefix):
        func_name = action_prefix + item_type.name
        if hasattr(self, func_name):
            return getattr(self, func_name)

        for field in item_type.fields():
            if not field.is_base_class:
                continue
            typ = field.type
            func_name = action_prefix + typ.name

            if hasattr(self, func_name):
                return getattr(self, func_name)

            return self.get_action_func(typ, action_prefix)

        return None

    def get_walk_func(self, item_type):
        return self.get_action_func(item_type, 'walk_')

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
        end_of_list = gdb.parse_and_eval('end_of_list').address
        item_list = val['list']
        nodetype = item_list.type.template_argument(0)
        cur_elt = item_list['first']
        children = []
        while cur_elt != end_of_list:
            info = cur_elt.dereference()['info']
            children.append(info.cast(nodetype.pointer()))
            cur_elt = cur_elt.dereference()['next']
        return children

ExpressionTraverser()

def PointerDisplay(value):
    return "({}) {}".format(value.type, value.format_string(raw = True))

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

        trait = "field = " + '.'.join(db_cata)

        return "{} {}".format(PointerDisplay(self.val), trait)

class ItemDerivedPrinter:
    "Print a pointer to MySQL Item derived class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return self.val.format_string(raw = True)

        val = self.val.cast(self.val.dynamic_type)
        return PointerDisplay(val)

class ItemPointerPrinter:
    "Print a pointer of MySQL base Item class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return self.val.format_string(raw = True)

        # Case the base pointer to derived class.
        val_derived = self.val.cast(self.val.dynamic_type)
        return str(val_derived) if val_derived.type != self.val.type else \
            self.val.format_string(raw = True)

class TableListPrinter:
    "Print a pointer of MySQL TABLE_LIST class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return self.val.format_string(raw = True)

        table_list = self.val.dereference()

        trait = ""
        if table_list['table_name'] and table_list['table_name'].string():
            trait = "table_name = " + table_list['table_name'].string()

        if table_list['nested_join']:
            trait += "nested join"

        return "{} {}".format(PointerDisplay(self.val), trait)

class MdlRequestPrinter:
    "Print a pointer of MySQL MDL_request class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return self.val.format_string(raw = True)

        mdl_request = self.val.dereference()

        trait = "type = {}, duration = {}, key = {}".format(
            mdl_request['type'], mdl_request['duration'],
            mdl_request['key'].address)

        return "{} {}".format(PointerDisplay(self.val), trait)

class MdlKeyPrinter:
    "Print a pointer of MySQL MDL_key class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        if not self.val:
            return self.val.format_string(raw = True)

        mdl_key = self.val.dereference()
        mdl_namespace = self.val['m_ptr'][0].cast(
            gdb.lookup_type('MDL_key::enum_mdl_namespace'))

        trait = "namespace = {}, m_ptr = {}".format(mdl_namespace,
                                                    mdl_key['m_ptr'])

        return "{} {}".format(PointerDisplay(self.val), trait)

def build_pretty_printer():
    pp = CustomRegexpCollectionPrettyPrinter(
        "mysqld")
    pp.add_printer('List', '^List<.*>$', MySQLListPrinter)
    pp.add_printer('Item_field *', '^Item_field \*$', ItemFieldPrinter)
    pp.add_printer('Item *', '^Item \*$', ItemPointerPrinter)
    pp.add_printer('Item_ *', '^Item_.* \*$', ItemDerivedPrinter)
    pp.add_printer('PT *', '^PT.* \*$', ItemDerivedPrinter)
    pp.add_printer('TABLE_LIST *', '^TABLE_LIST \*$', TableListPrinter)
    pp.add_printer('MDL_request *', '^MDL_request \*$', MdlRequestPrinter)
    pp.add_printer('MDL_key *', '^MDL_key \*$', MdlKeyPrinter)
    return pp

gdb.printing.register_pretty_printer(
    gdb.current_objfile(),
    build_pretty_printer(),
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

        return "{} {}".format(PointerDisplay(self.val), trait)

class ItemIntPrinter:
    "Print a pointer to MySQL Item_int class"
    def __init__(self, val):
        self.val = val

    def to_string(self):
        val_derived = self.val.cast(self.val.dynamic_type)
        item = val_derived.dereference()
        trait = "value = " + str(item['value'])

        return "{} {}".format(PointerDisplay(val_derived), trait)

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
