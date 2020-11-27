# Regard all the files you debug during this GDB session will come from trusted resources
set auto-load safe-path /

# Increase the limitation of elements' number
set print elements 2000

# Print object in a pretty way
set print pretty on

# When printing a pointer to object, print its subclass' type
set print object

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

define polar
  dont-repeat
  file /flash12/hope.lb/Documents/Codes/PolarDB_80/runtime_output_directory/mysqld
  run --defaults-file=/flash12/hope.lb/bin/my-33332.cnf --gdb --debug
end

define polar20
  dont-repeat
  file /flash12/hope.lb/Documents/Codes/master-2.0/bld_Debug/runtime_output_directory/mysqld
  run --defaults-file=/flash12/hope.lb/bin/my-28342.cnf --gdb --debug
end

# Debug mysql server.
define mysql
  dont-repeat
  if $argc == 0
    help mysql
  else
    file runtime_output_directory/mysqld
    run --defaults-file=$arg0 --gdb --debug
  end
end
document mysql
Debug an instance of mysql server.
Usage: mysql cnf_file
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

# Mysql tool
source ~/mysqld-gdb.py

# Std tool
source ~/std-gdb.py
