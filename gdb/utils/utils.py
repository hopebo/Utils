#!/usr/bin/python

import gdb

def RawDisplay(value):
    if hasattr(gdb.Value, 'format_string'):
        info = value.format_string(raw = True)
    else:
        if value.dynamic_type.code == gdb.TYPE_CODE_PTR:
            # Cast pointer type to void * to avoid pretty printer
            t_void = gdb.lookup_type("void")
            info = str(value.cast(t_void.pointer()))

    return "({}) {}".format(value.dynamic_type, info)

def AdaptDisplay(value):
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

"""
Utilities to find type name and extract value from std containers.
"""
def get_value_from_aligned_membuf(buf, valtype):
    """Returns the value held in a __gnu_cxx::__aligned_membuf."""
    return buf['_M_storage'].address.cast(valtype.pointer()).dereference()

def get_value_from_Rb_tree_node(node):
    """Returns the value held in an _Rb_tree_node<_Val>"""
    try:
        member = node.type.fields()[1].name
        if member == '_M_value_field':
            # C++03 implementation, node contains the value as a member
            return node['_M_value_field']
        elif member == '_M_storage':
            # C++11 implementation, node stores value in __aligned_membuf
            valtype = node.type.template_argument(0)
            return get_value_from_aligned_membuf(node['_M_storage'], valtype)
    except:
        pass
    raise ValueError("Unsupported implementation for %s" % str(node.type))

# Starting with the type ORIG, search for the member type NAME.  This
# handles searching upward through superclasses.  This is needed to
# work around http://sourceware.org/bugzilla/show_bug.cgi?id=13615.
def find_type(orig, name):
    typ = orig.strip_typedefs()
    while True:
        # Use Type.tag to ignore cv-qualifiers.  PR 67440.
        search = '%s::%s' % (typ.tag, name)
        try:
            return gdb.lookup_type(search)
        except RuntimeError:
            pass
        # The type was not found, so try the superclass.  We only need
        # to check the first superclass, so we don't bother with
        # anything fancier here.
        fields = typ.fields()
        if len(fields) and fields[0].is_base_class:
            typ = fields[0].type
        else:
            raise ValueError("Cannot find type %s::%s" % (str(orig), name))

_versioned_namespace = '__8::'

def lookup_templ_spec(templ, *args):
    """
    Lookup template specialization templ<args...>
    """
    t = '{}<{}>'.format(templ, ', '.join([str(a) for a in args]))
    try:
        return gdb.lookup_type(t)
    except gdb.error as e:
        # Type not found, try again in versioned namespace.
        global _versioned_namespace
        if _versioned_namespace and _versioned_namespace not in templ:
            t = t.replace('::', '::' + _versioned_namespace, 1)
            try:
                return gdb.lookup_type(t)
            except gdb.error:
                # If that also fails, rethrow the original exception
                pass
        raise e

# Use this to find container node types instead of find_type,
# see https://gcc.gnu.org/bugzilla/show_bug.cgi?id=91997 for details.
def lookup_node_type(nodename, containertype):
    """
    Lookup specialization of template NODENAME corresponding to CONTAINERTYPE.
    e.g. if NODENAME is '_List_node' and CONTAINERTYPE is std::list<int>
    then return the type std::_List_node<int>.
    Returns None if not found.
    """
    # If nodename is unqualified, assume it's in namespace std.
    if '::' not in nodename:
        nodename = 'std::' + nodename
    try:
        valtype = find_type(containertype, 'value_type')
    except:
        valtype = containertype.template_argument(0)
    valtype = valtype.strip_typedefs()
    try:
        return lookup_templ_spec(nodename, valtype)
    except gdb.error as e:
        # For debug mode containers the node is in std::__cxx1998.
        if is_member_of_namespace(nodename, 'std'):
            if is_member_of_namespace(containertype, 'std::__cxx1998',
                                      'std::__debug', '__gnu_debug'):
                nodename = nodename.replace('::', '::__cxx1998::', 1)
                try:
                    return lookup_templ_spec(nodename, valtype)
                except gdb.error:
                    pass
        return None

def is_member_of_namespace(typ, *namespaces):
    """
    Test whether a type is a member of one of the specified namespaces.
    The type can be specified as a string or a gdb.Type object.
    """
    if type(typ) is gdb.Type:
        typ = str(typ)
    typ = strip_versioned_namespace(typ)
    for namespace in namespaces:
        if typ.startswith(namespace + '::'):
            return True
    return False

"""
Iterator to get values from StdMap
"""
class RbtreeIterator(object):
    """
    Turn an RB-tree-based container (std::map, std::set etc.) into
    a Python iterable object.
    """

    def __init__(self, rbtree):
        self.size = rbtree['_M_t']['_M_impl']['_M_node_count']
        self.node = rbtree['_M_t']['_M_impl']['_M_header']['_M_left']
        self.count = 0

        # Extra info to cast type
        self.ptype = lookup_node_type('_Rb_tree_node', rbtree.type).pointer()

    def __iter__(self):
        return self

    def __len__(self):
        return int (self.size)

    def __next__(self):
        if self.count == self.size:
            raise StopIteration
        result = self.node
        self.count = self.count + 1
        if self.count < self.size:
            # Compute the next node.
            node = self.node
            if node.dereference()['_M_right']:
                node = node.dereference()['_M_right']
                while node.dereference()['_M_left']:
                    node = node.dereference()['_M_left']
            else:
                parent = node.dereference()['_M_parent']
                while node == parent.dereference()['_M_right']:
                    node = parent
                    parent = parent.dereference()['_M_parent']
                if node.dereference()['_M_right'] != parent:
                    node = parent
            self.node = node

        result = result.cast(self.ptype).dereference()
        # Return the pair type
        result = get_value_from_Rb_tree_node(result)
        return result

def traverse_std_map(val):
    myiter = RbtreeIterator(val)

    for n in myiter:
        print(n['first'])
        print(n['second'])

"""
Iterator to get values from StdUnorderedMap
"""
class StdHashtableIterator(object):
    def __init__(self, unordered_map):
        # Extrace hash table from map object
        hashtable = unordered_map['_M_h']

        self.node = hashtable['_M_before_begin']['_M_nxt']
        valtype = hashtable.type.template_argument(1)
        cached = hashtable.type.template_argument(9).template_argument(0)
        node_type = lookup_templ_spec('std::__detail::_Hash_node', str(valtype),
                                      'true' if cached else 'false')
        self.node_type = node_type.pointer()

    def __iter__(self):
        return self

    def __next__(self):
        if self.node == 0:
            raise StopIteration
        elt = self.node.cast(self.node_type).dereference()
        self.node = elt['_M_nxt']
        valptr = elt['_M_storage'].address
        valptr = valptr.cast(elt.type.template_argument(0).pointer())
        return valptr.dereference()

def traverse_std_unordered_map(val):
    myiter = StdHashtableIterator(val)

    for n in myiter:
        print(n['first'])
        print(n['second'])

def traverse_std_vector(vec):
    array = []

    item = vec['_M_impl']['_M_start']
    while item != vec['_M_impl']['_M_finish']:
        array.append(item.dereference())
        item += 1

    return array
