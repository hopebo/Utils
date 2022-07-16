# Regard all the files you debug during this GDB session will come from trusted resources
set auto-load safe-path /

# Increase the limitation of elements' number
set print elements 2000

# Print object in a pretty way
set print pretty on

# When printing a pointer to object, print its subclass' type
set print object

# When printing an array, display the values of arrays using longer multi-line format.
# Otherwise in a simple one-line format.
set print array on

# Support non-stop mode. Current thread stop, other threads go.
# Must be set before attaching to program.
# If using the CLI, pagination breaks non-stop.
set pagination off

# Finally, turn it on!
set non-stop on

# Alias of enable and disable
define e
  dont-repeat
  if $argc == 0
    enable
  else
    enable $arg0
  end
end

define de
  dont-repeat
  if $argc == 0
    disable
  else
    disable $arg0
  end
end

define mysql13
  dont-repeat
  file /PATH/runtime_output_directory/mysqld
  run --defaults-file=/PATH/my.cnf --gdb --debug
end

# Debug mysql server.
define server
  dont-repeat
  if $argc == 0
    help server
  else
    file runtime_output_directory/mysqld
    run --defaults-file=$arg0 --gdb --debug
  end
end
document server
Debug an instance of mysql server.
Usage: server cnf_file
end

# examine(x) x/<n/f/u> <addr>
# n number of address unit
# f display format
#   x hexadecimal
#   d decimal
#   t binary
#   c character
#   f float
# u size of address unit
#   b single byte
#   h two bytes
#   w four bytes
#   h eight bytes

define saveb
  dont-repeat
  save breakpoints gdb.bp
end

define loadb
  dont-repeat
  source gdb.bp
end

define lock
  dont-repeat
  set scheduler-locking on
end

define unlock
  dont-repeat
  set scheduler-locking off
end

define dp
  dont-repeat
  disable pretty-printer
end

define ep
  dont-repeat
  enable pretty-printer
end

python
import sys
import os
sys.path.insert(0, os.path.expanduser('/PATH/Utils/gdb/'))
end

# Mysql tool
source /PATH/Utils/gdb/mysqld-gdb.py

# Import stdlib pretty printer
python
import sys
import os
sys.path.insert(0, os.path.expanduser('/PATH/Utils/gdb/libstdc++-v3'))
from libstdcxx.v6.printers import register_libstdcxx_printers
end
