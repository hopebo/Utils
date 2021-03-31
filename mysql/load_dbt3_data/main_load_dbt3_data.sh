#!/bin/bash
#
# Declare this script's functions and contents.

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -s SOCKET                 MySQL socket file.
  -d DSS_PATH               DBT3 data directory.
  -h                        Print this message and exit.

This script is intended to generate bash script template.
EOF
}

BASEPATH=$(cd `dirname $0`; pwd)

while getopts "s:d:h" opt; do
    case $opt in
        s)
            SOCKET=$OPTARG
            ;;
        d)
            DSS_PATH=$OPTARG
            ;;
        h)
            usage
            exit 0
            ;;
        \?)
            usage
            exit 1
            ;;
    esac
done

DBNAME="dbt3"

MYSQL_CMD="mysql -u root --socket=${SOCKET}"
MYSQL_IMPORT="mysqlimport -u root --socket=${SOCKET}"

eval ${MYSQL_CMD} -e "\"DROP DATABASE IF EXISTS ${DBNAME}\""
eval ${MYSQL_CMD} -e "\"CREATE DATABASE ${DBNAME}\""

export MYSQL_CMD="${MYSQL_CMD} -D ${DBNAME} "
export MYSQL_IMPORT
export DSS_PATH
export DBNAME

bash dbt3-mysql-create-tables
bash dbt3-mysql-load-data
