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
