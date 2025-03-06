#!/usr/bin/python
# -*- coding: utf-8 -*-

# The following command can perform the same effect.
# for i in `ls *.tbl`; do sed 's/|$//' $i > ${i/tbl/csv}; echo $i; done;

import os
import re

source_data = "/flash12/hope.lb/data/dbt3-1G-data"
target_data = "/flash12/hope.lb/data/dbt3-1G-data-pg"

data_files = os.listdir(source_data)

for filename in data_files:
    source_data_path = source_data + "/" + filename
    print(source_data_path)

    target_data_path = target_data + "/" + filename

    if (os.path.isdir(source_data_path)):
        continue

    source_data_file_object = open(source_data_path, "r")
    target_data_file_object = open(target_data_path, "w")

    for line in source_data_file_object.readlines():
        line = line.strip()
        line = line[0 : len(line) - 1] + "\n"

        target_data_file_object.write(line)

    source_data_file_object.close()
    target_data_file_object.close()
