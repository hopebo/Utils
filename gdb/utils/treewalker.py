import gdb
import utils.convenience_variable as cv
from utils.display import AdaptDisplay

'''
Base class for Tree-like structure traverse.
'''
class TreeWalker(object):
    def __init__(self):
        self.cv_prefix = None
        self.count = 0
        self.level_graph = []

    def walk(self, expr, mark_val = None):
        self.cv_prefix = cv.get_convenience_name()
        self.count = 0
        self.level_graph = []
        self.mark_val = mark_val

        # Recursively walk children elements
        self.do_walk(expr, 0)

    def do_walk(self, expr, level):
        expr_dtype, expr_casted = self.customized_cast_type(expr)

        # Prefix graph symbols like |  |  `--
        heading_level_graph = '  '.join(self.level_graph[:level])

        # Set convenience variable
        cv_name = "%s%d" % (self.cv_prefix, self.count)
        cv.gdb_set_convenience_variable(cv_name, expr_casted)
        self.count += 1

        show_func = self.get_show_func(expr_dtype.target())

        if show_func is None:
            expr_info = AdaptDisplay(expr_casted)
        else:
            expr_info = show_func(expr_casted)

        print("{}{}{}{}".format(
            heading_level_graph, '' if level == 0 else '--',
            cv.gdb_print_cv(cv_name, expr_info),
            '  <-' if expr == self.mark_val else ''))

        # If all the elements on the previous level have been printed, we don't
        # need to add `|` in front of nested elements' printing.
        if level - 1 >= 0 and self.level_graph[level - 1] == '`':
            self.level_graph[level - 1] = ' '

        walk_func = self.get_walk_func(expr_dtype.target())
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
                # If it's the last child in current level, use '`' to terminate.
                self.level_graph[level] = '`'
            self.do_walk(child, level + 1)

    def get_action_func(self, item_type, action_prefix):
        # Use Type.tag instead of Type.name to be compatible with lower version
        if hasattr (item_type, "name"):
            type_name = item_type.name
        else:
            type_name = item_type.tag

        func_name = action_prefix + type_name.replace('::', '_')
        if hasattr(self, func_name):
            return getattr(self, func_name)

        for field in item_type.fields():
            if not field.is_base_class:
                continue
            typ = field.type
            # Replace namespace '::' with '_', which can compose a valid
            # function name
            func_name = action_prefix + typ.tag.replace('::', '_')

            if hasattr(self, func_name):
                return getattr(self, func_name)

            return self.get_action_func(typ, action_prefix)

        return None

    # Derived class should implement function with specific name walk_typename
    # to get its children.
    def get_walk_func(self, item_type):
        return self.get_action_func(item_type, 'walk_')

    # Customized show function instead of pretty printer.
    def get_show_func(self, item_type):
        return self.get_action_func(item_type, 'show_')

    # Customized function to cast data to target type
    def customized_cast_type(self, expr):
        expr_dtype = expr.dynamic_type
        expr_casted = expr.cast(expr_dtype)
        return expr_dtype, expr_casted
