#!/bin/bash
#
# Declare this script's functions and contents.

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -p PORT                   PostgreSQL server's port number.
  -d DSS_PATH               DBT3 data directory.
  -h                        Print this message and exit.

This script is intended to generate bash script template.
EOF
}

BASEPATH=$(cd `dirname $0`; pwd)

while getopts "p:d:h" opt; do
    case $opt in
        p)
            PORT=$OPTARG
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

LOCAL_PG_PARAM="-p ${PORT}"
DBNAME="dbt3"

createdb ${LOCAL_PG_PARAM} ${DBNAME}

export LOCAL_PG_PARAM="${LOCAL_PG_PARAM} -d ${DBNAME}"
export DSS_PATH

bash dbt3-pgsql-create-tables
bash dbt3-pgsql-load-data
