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
  -U USER                   User name.
  -H HOST                   Host address.
  -h                        Print this message and exit.

EOF
}

BASEPATH=$(cd `dirname $0`; pwd)

PORT=5432
HOST="localhost"
USER="postgres"

while getopts "p:d:U:H:h" opt; do
    case $opt in
        p)
            PORT=$OPTARG
            ;;
        d)
            DSS_PATH=$OPTARG
            ;;
        U)
            USER=$OPTARG
            ;;
        H)
            HOST=$OPTARG
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

PG_CONNECT_PARAM="-h ${HOST} -p ${PORT} -U ${USER}"
DBNAME="dbt3"

createdb ${PG_CONNECT_PARAM} ${DBNAME}

export PG_CONNECT_PARAM="${PG_CONNECT_PARAM} -d ${DBNAME}"
export DSS_PATH

bash dbt3-pgsql-create-tables
bash dbt3-pgsql-load-data
