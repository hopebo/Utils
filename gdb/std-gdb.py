#!/usr/bin/python
from __future__ import print_function # python2.X support
import re
import itertools

if sys.version_info[0] > 2:
    ### Python 3 stuff
    Iterator = object
    # Python 3 folds these into the normal functions.
    imap = map
    izip = zip
    # Also, int subsumes long
    long = int
else:
    ### Python 2 stuff
    class Iterator:
        """Compatibility mixin for iterators
        Instead of writing next() methods for iterators, write
        __next__() methods and use this mixin to make them work in
        Python 2 as well as Python 3.
        Idea stolen from the "six" documentation:
        <http://pythonhosted.org/six/#six.Iterator>
        """

        def next(self):
            return self.__next__()

    # In Python 2, we still need these from itertools
    from itertools import imap, izip

# TODO: The convenience name utility relies on mysqld-gdb.py.

"""
std::vector pretty printer.
"""
regex_std_vector = re.compile(r"^std::vector<.*>$")
class StdVectorPrinter:
    "Print a std::vector"

    class _iterator(Iterator):
        def __init__ (self, start, finish, bitvec):
            self.bitvec = bitvec
            if bitvec:
                self.item   = start['_M_p']
                self.so     = start['_M_offset']
                self.finish = finish['_M_p']
                self.fo     = finish['_M_offset']
                itype = self.item.dereference().type
                self.isize = 8 * itype.sizeof
            else:
                self.item = start
                self.finish = finish
                self.count = 0
            self.convenience_name_prefix = get_convenince_name()

        def __iter__(self):
            return self

        def __next__(self):
            count = self.count
            self.count = self.count + 1
            convenince_name = get_array_index_name(self.convenience_name_prefix, count)
            if self.bitvec:
                if self.item == self.finish and self.so >= self.fo:
                    raise StopIteration
                elt = self.item.dereference()
                if elt & (1 << self.so):
                    obit = 1
                else:
                    obit = 0
                    self.so = self.so + 1
                if self.so >= self.isize:
                    self.item = self.item + 1
                    self.so = 0
                gdb_set_convenience_variable(convenince_name, obit)
                return ('%s' % convenince_name, obit)
            else:
                if self.item == self.finish:
                    raise StopIteration
                elt = self.item.dereference()
                self.item = self.item + 1
                gdb_set_convenience_variable(convenince_name, elt)
                return ('$%s' % convenince_name, elt)

    def __init__(self, typename, val):
        self.typename = typename
        self.val = val
        self.is_bool = val.type.template_argument(0).code  == gdb.TYPE_CODE_BOOL

    def children(self):
        return self._iterator(self.val['_M_impl']['_M_start'],
                              self.val['_M_impl']['_M_finish'],
                              self.is_bool)

    def to_string(self):
        start = self.val['_M_impl']['_M_start']
        finish = self.val['_M_impl']['_M_finish']
        end = self.val['_M_impl']['_M_end_of_storage']
        if self.is_bool:
            start = self.val['_M_impl']['_M_start']['_M_p']
            so    = self.val['_M_impl']['_M_start']['_M_offset']
            finish = self.val['_M_impl']['_M_finish']['_M_p']
            fo     = self.val['_M_impl']['_M_finish']['_M_offset']
            itype = start.dereference().type
            bl = 8 * itype.sizeof
            length   = (bl - so) + bl * ((finish - start) - 1) + fo
            capacity = bl * (end - start)
            return ('%s<bool> of length %d, capacity %d'
                    % (self.typename, int (length), int (capacity)))
        else:
            return ('%s of length %d, capacity %d'
                    % (self.typename, int (finish - start), int (end - start)))

from gdb.printing import PrettyPrinter, register_pretty_printer
class CustomPrettyPrinterLocator(PrettyPrinter):
    """Given a gdb.Value, search for a custom pretty printer"""

    def __init__(self):
        super(CustomPrettyPrinterLocator, self).__init__(
            "std-pretty-printers", []
        )

    def __call__(self, val):
        """Return the custom formatter if the type can be handled"""

        typename = gdb.types.get_basic_type(val.type).tag
        if typename is None:
            typename = val.type.name

        if regex_std_vector.match(str(typename)):
            return StdVectorPrinter(typename, val)


register_pretty_printer(None, CustomPrettyPrinterLocator(), replace=True)
