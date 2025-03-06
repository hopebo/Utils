#!/usr/bin/python3

import argparse
import os
import sys
import re
import time
import subprocess

parser = argparse.ArgumentParser(allow_abbrev=True,
    description='Normalize multi-thread compilation log making it suitable for compildb',
    epilog=f'For example: {os.path.basename(sys.argv[0])} -i /local/compilation.log '\
    '-w /local/workdirectory')

parser.add_argument('-i', '--input', help='input compilation file', required=True)

parser.add_argument('-w', '--directory', help='work directory', required=True)

def search_file(relpath, directory):
    """Searches for a file in a given directory and its subdirectories."""

    filename = os.path.basename(relpath)
    for root, dirs, files in os.walk(directory):
        if filename in files:
            abspath = os.path.join(root, filename)
            if abspath.endswith(relpath):
                return abspath
    return None

def remove_trailing_relative_path(absolute_path, relative_path):
    # Normalize paths
    abs_path = os.path.normpath(absolute_path)
    rel_path = os.path.normpath(relative_path)

    # Split paths into components
    abs_parts = abs_path.split(os.sep)
    rel_parts = rel_path.split(os.sep)

    # Check if relative path is at the end of absolute path
    if abs_parts[-len(rel_parts):] == rel_parts:
        # Remove the relative path parts
        result = os.sep.join(abs_parts[:-len(rel_parts)])
        # Ensure the result is not empty (for root directory)
        return result if result else os.sep
    else:
        raise Exception()  # Return original path if no match

def remove_leading_dots(path):
    normalized = os.path.normpath(path)
    parts = normalized.split(os.sep)
    while parts and parts[0] in ('.', '..'):
        parts.pop(0)
    return os.sep.join(parts)

class Colors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def count_time(begin_time):
    cur_time = time.time()
    m, s = divmod(cur_time - begin_time, 60)
    if m >= 1:
        time_string = '{} min {} sec'.format(int(m), int(s))
    else:
        time_string = '{} sec'.format(int(s))

    print(f'{Colors.WHITE}Spending {time_string} '\
          f'{Colors.END}', flush=True)

cmd_args = vars(parser.parse_args())

input_f = cmd_args['input']
directory = cmd_args['directory']

output_f = os.path.join(directory, 'normalized_compilation.log')
output_fs = open(output_f, 'w')

pattern = r'.*(gcc|g\+\+).+ -o (.+\.o) (.+\.cp{,2}).*'
prog = re.compile(pattern)

print(f"{Colors.GREEN}Parsing compilation log...{Colors.END}", flush=True)
begin_time = time.time()

with open(input_f, 'r') as f:
    line = f.readline()
    while line:
        result = prog.match(line)
        if result:
            source_file = remove_leading_dots(result.group(3))

            location = search_file(source_file, directory)
            try:
                if location:
                    file_dir = remove_trailing_relative_path(location, source_file)
                    enter_str = f"make[2]: Entering directory '{file_dir}'\n"

                    output_fs.write(enter_str)
                    output_fs.write(f'{result.group(0)}\n')
                else:
                    print(f'Source file {source_file} not found.', flush=True)
            except:
                print(location)
                print(source_file)

        line = f.readline()

count_time(begin_time)

output_fs.close()

print(f"{Colors.GREEN}Generating compile_commands.json file...{Colors.END}", flush=True)
begin_time = time.time()

command = f"compiledb --parse {output_f} "\
    f"--output {os.path.join(directory, 'compile_commands.json')}"

print(command, flush=True)
result = subprocess.run(command, shell=True, stderr=subprocess.STDOUT)

count_time(begin_time)
