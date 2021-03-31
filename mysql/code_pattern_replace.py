#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re

directory = "/flash12/hope.lb/Documents/Codes/PolarDB_80/sql"

source_files = os.listdir(directory)

clone_pattern = re.compile(r".*clone_new_item.*")

items_map = {}

for filename in source_files:
    filepath = directory + "/" + filename
    #filepath = "/flash12/hope.lb/Documents/Codes/PolarDB_80/sql/item_func.h"

    if (os.path.isdir(filepath)):
        continue

    file_object = open(filepath, "r")
    lines = file_object.readlines()
    new_content = ""

    i = 0
    while i < len(lines):
        line = lines[i]
        code_trunk_begin = False
        code_trunk_end = False
        left_parantheses = 0
        if (clone_pattern.search(line)):
            new_code = ""
            except_first_line = ""
            first_line = True
            while i < len(lines):
                new_code += lines[i]
                if not first_line:
                    except_first_line += lines[i]
                else:
                    first_line = False

                j = 0
                while j < len(lines[i]):
                    if lines[i][j] == '{':
                        left_parantheses += 1
                    elif lines[i][j] == '}':
                        left_parantheses -= 1
                    j += 1

                if left_parantheses == 0:
                    break;
                else:
                    i += 1

            new_code = new_code.replace('(thd->mem_root) ', '')
            except_first_line = except_first_line.replace('(thd->mem_root) ', '')

            if except_first_line.find('thd') == -1:
                print except_first_line
                print "not exist"
                new_code = new_code.replace('thd', '')
                print new_code

            new_content += new_code
        else:
            new_content += line

        i += 1

    file_object.close()

    with open(filepath, 'w') as f:
        f.write(new_content)
