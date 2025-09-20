#!/usr/bin/python3

import argparse
import os
import sys
import re
import json

parser = argparse.ArgumentParser(allow_abbrev=True,
    description='Adapt compile_commands.json in build directory to source file '\
                                 'directory, expand unity build if needed.',
    epilog=f'For example: {os.path.basename(sys.argv[0])} -b build_dir '\
    '-s source_dir')

parser.add_argument('-b', '--build_dir', help='build directory', required=True)

parser.add_argument('-s', '--source_dir', help='source directory')

cmd_args = vars(parser.parse_args())

build_dir = os.path.realpath(cmd_args['build_dir'])
src_dir = os.path.realpath(cmd_args['source_dir'])

compile_json = os.path.join(build_dir, 'compile_commands.json')

if not os.path.exists(compile_json):
    raise Exception(f"File {compile_json} does not exist")

def replace_path(string, original_path, target_path):
    def replace_group(match):
        if os.path.exists(target_path + match.group(3)):
            return f'{match.group(1)}{target_path}{match.group(3)}'
        else:
            return f'{match.group(0)}'

    pattern = fr'(\S*)({original_path})(\S*)'
    prog = re.compile(pattern)
    result = prog.sub(replace_group, string)
    return result

def expand_unity_build_item(item):
    res = []
    ub_file = item['file']
    ub_file_name = os.path.basename(ub_file)

    with open(ub_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            match = re.match(r'#include <(.*)>', line)
            if match is None:
                continue

            included_file = os.path.basename(match.group(1))
            new_item = item.copy()
            for key in new_item:
                new_item[key] = re.sub(fr'{ub_file_name}', included_file, new_item[key])

            res.append(new_item)

    return res

def refine_compile_json(build_dir, target_dir=None):
    with open(os.path.join(build_dir, 'compile_commands.json'), 'r') as f:
        data = json.load(f)

    i = 0
    while i < len(data):
        filename = os.path.basename(data[i]['file'])
        # Unity Build file
        if filename.startswith('ub_'):
            data.extend(expand_unity_build_item(data[i]))
            del data[i]
            continue

        if target_dir is None:
            i += 1
            continue

        for key in data[i]:
            data[i][key] = replace_path(data[i][key], build_dir, target_dir)
        i += 1


    with open(os.path.join(target_dir if target_dir else build_dir,
                           'compile_commands.json'), 'w') as f:
        json.dump(data, f, indent=2)

if src_dir:
    refine_compile_json(build_dir, src_dir)

refine_compile_json(build_dir)
