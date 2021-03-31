#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import Queue

class ItemInfo:
    def __init__(self, cloneImplement = "Unknown"):
        self.derivedItems = []
        self.baseItems = []
        self.cloneImplement = cloneImplement
        self.degree = -1
        self.paint = False
        return

    def gatherAttrs(self):
        return ",".join("{}={}".format(k, getattr(self, k))
                        for k in self.__dict__.keys())

    def __str__(self):
        return "[{}:{}]".format(self.__class__.__name__, self.gatherAttrs())

def GetDerivedClassName(derived_class_str):
    derived_class_str = derived_class_str.strip().split()
    class_name = ""
    for chunk in derived_class_str:
        chunk = chunk.strip()
        if chunk == "class" or chunk == "final":
            continue
        else:
            class_name = chunk

    assert class_name
    return class_name

def GetBaseClassesName(base_classes_str):
    base_classes_str = base_classes_str.strip().split()
    classes_name = []
    for chunk in base_classes_str:
        chunk = chunk.strip().strip(',')
        if chunk == "public" or chunk == "private" or chunk == "protected" or \
           chunk == ",":
            continue
        else:
            classes_name.append(chunk)

    assert classes_name
    return classes_name

color = '''skinparam class {
  BackgroundColor<<Implemented>> green
  BackgroundColor<<Unimplemented>> red
  BackgroundColor<<Unknown>> wheat
}\n'''

def PaintUML(items_map):
    classes_name = ""
    inheritance = ""
    for item in items_map.keys():
        classes_name += "class " + item + " <<" + \
            items_map[item].cloneImplement + ">>\n"

        for base_item in items_map[item].derivedItems:
            inheritance += item + " <|-- " + base_item + "\n"

    print (color + classes_name + inheritance)
    return

class UMLContent:
    def __init__(self):
        self.color = '''skinparam class {
  BackgroundColor<<Implemented>> green
  BackgroundColor<<Unimplemented>> red
  BackgroundColor<<Unknown>> wheat
}\n'''

        self.Initialize()
        return

    def Initialize(self, item = "", limit = 1000):
        self.classesName = ""
        self.inheritance = ""
        self.root_item = item
        self.limit = limit
        self.implemented = 0
        self.unimplemented = 0
        self.unknown = 0
        return

    def Print(self):
        if not self.inheritance:
            return
        print ("@startuml")
        print (self.color + self.classesName + self.inheritance)
        print ("note \"Implemented: {0}, Unimplemented: {1}, Rate: {0}/{2}\" as N1".
               format(self.implemented, self.unimplemented, self.implemented +
                      self.unimplemented))
        print ("@enduml")

def ConstructUML(items_map, item, uml):
    uml.classesName += "class " + item + " <<" + \
        items_map[item].cloneImplement + ">>\n"

    if items_map[item].cloneImplement == "Implemented":
        uml.implemented += 1
    elif items_map[item].cloneImplement == "Unimplemented":
        uml.unimplemented += 1
    else:
        uml.unknown += 1

    i = 0
    while i < len(items_map[item].derivedItems):
        if item == current_item and uml.limit < 0:
            break

        derived_item = items_map[item].derivedItems[i]

        if items_map[derived_item].paint != True:
            uml.limit -= 1
            uml.inheritance += item + " <|-- " + derived_item + "\n"
            ConstructUML(items_map, derived_item, uml)

        i += 1

    if i >= len(items_map[item].derivedItems):
        items_map[item].paint = True
    return


directory = "/flash12/hope.lb/Documents/Codes/PolarDB_80/sql"

source_files = os.listdir(directory)

pattern = re.compile(r"^class .*[Ii]tem.*[^;]$")
pq_clone_pattern = re.compile(r"pq_clone_item")

items_map = {}

for filename in source_files:
    filepath = directory + "/" + filename
    #filepath = "/flash12/hope.lb/Documents/Codes/PolarDB_80/sql/item.h"

    if (os.path.isdir(filepath)):
        continue

    file_object = open(filepath, "r")
    lines = file_object.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        class_def_header = ""
        class_def = ""

        if (pattern.search(line)):
            class_range_begin = False
            class_range_end = False
            left_parantheses = 0
            while i < len(lines) and not class_range_end:
                next_line = lines[i]

                j = 0
                while j < len(next_line):
                    if next_line[j] == '{':
                        if not class_range_begin:
                            class_range_begin = True
                            class_def_header = class_def + next_line[0 : j]
                        left_parantheses += 1
                    elif next_line[j] == '}':
                        left_parantheses -= 1
                        if class_range_begin and left_parantheses == 0:
                            class_range_end = True
                            break

                    j += 1

                if class_range_end:
                    class_def += next_line[0 : j + 1]
                else:
                    class_def += next_line

                i += 1

            classes_str = class_def_header.split(':')
            if len(classes_str) > 2:
                print (filepath)
                print (class_def_header)
                continue
            #assert len(classes_str) <= 2

            derived_class_str = classes_str[0]
            derived_class = GetDerivedClassName(derived_class_str)

            base_classes = []
            if len(classes_str) == 2:
                base_classes_str = classes_str[1]
                base_classes = GetBaseClassesName(base_classes_str)

            pq_clone_implemented = "Unimplemented"
            if (pq_clone_pattern.search(class_def)):
                pq_clone_implemented = "Implemented"

            if items_map.has_key(derived_class):
                items_map[derived_class].cloneImplement = pq_clone_implemented
            else:
                items_map[derived_class] = ItemInfo(pq_clone_implemented)

            for base_class in base_classes:
                if not items_map.has_key(base_class):
                    items_map[base_class] = ItemInfo()

                items_map[base_class].derivedItems.append(derived_class)
                items_map[derived_class].baseItems.append(base_class)

            #print (class_def_header)
            #print (class_def)

        i += 1

    #break

root_items = (["Item_bool_func"],
              ["Item_basic_constant"],
              ["Item_sum"],
              ["Item_real_func"],
              ["Item_temporal_func"],
              ["Item_geometry_func"],
              ["Item_func_numhybrid"],
              ["Item_json_func"],
              ["Item_str_ascii_func"],
              ["Item_int_func"],
              ["Item_str_func"],
              ["Item_func"],
              ["Item_result_field"],
              ["Item"],
              ["Parse_tree_node"])
#for item in items_map.keys():
#    print (item)
#    print (items_map[item])

def CalculateDegreeHelper(items_map, item):
    if items_map[item].degree == -1:
        items_map[item].degree = 1
        for derived_item in items_map[item].derivedItems:
            items_map[item].degree += CalculateDegreeHelper(items_map, derived_item)
    return items_map[item].degree

def CalculateDegree(items_map):
    for item in items_map.keys():
        CalculateDegreeHelper(items_map, item)
    return

def Prune(items_map, item, num):
    for base_item in items_map[item].baseItems:
        items_map[base_item].degree -= num
        Prune(items_map, base_item, num)
    return

CalculateDegree(items_map)

uml = UMLContent()

limit = 1000
for j in root_items:
    item = j[0]
    current_item = item
    if item == "Item_int_func":
        limit = 60

    uml.Initialize(item, limit)
    ConstructUML(items_map, item, uml)
    uml.Print()

    if item == "Item_int_func":
        limit = 1000
        uml.Initialize(item, limit)
        ConstructUML(items_map, item, uml)
        uml.Print()

    Prune(items_map, item, items_map[item].degree)

test = []
for item in items_map.keys():
    test.append((items_map[item].degree, item))

test.sort(reverse = True)
for mm in test:
    print (mm)

for degree, item in test:
    uml.Initialize(item, limit)
    ConstructUML(items_map, item, uml)
    uml.Print()

#PaintUMLHelper(items_map, "Item_int_func")

print (items_map['Item_result_field'].derivedItems)
print (items_map['Item_subselect'].derivedItems)
print (items_map['Item_sum_hybrid_field'].derivedItems)

implemented = 0
unimplemented = 0
unknown = 0
count = 0
for item in items_map.keys():
    count += 1
    if items_map[item].cloneImplement == "Implemented":
        implemented += 1
    elif items_map[item].cloneImplement == "Unimplemented":
        unimplemented += 1
    else:
        unknown += 1

print (implemented, unimplemented, unknown, count)
