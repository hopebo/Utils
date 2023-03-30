#!/bin/bash

usage() {
    echo "usage: gen-pg-cnf-with-alias.sh [-ag] [-b install_dir] [-d data_dir]"
    echo "  [-p port] [-o output_dir]"
    echo ""
    echo " b - pgsql installation directory"
    echo " d - pgsql data directory"
    echo " p - port number the server listens on"
    echo " o - generated files saving directory"
    echo " g - start mysqld with gdb"
    echo " a - generate pgsql alias file"
    exit 1
}

realpath() {
    PATH=$1
    if [[ "${PATH:0:1}" = "/" ]]; then
        echo ${PATH}
    elif [[ "${PATH:0:1}" = "~" ]] && [[ "${PATH:1:1}" = "/" ]]; then
        echo /home/${USER}${PATH:1}
    else
        echo `pwd`/${PATH}
    fi
}

OUTPUT_DIR=~
PORT=5432

while getopts "b:d:p:o:ga" opt; do
    case $opt in
        b)
            INSTALL_DIR=${OPTARG}
            ;;
        d)
            DATA_DIR=${OPTARG}
            ;;
        p)
            PORT=${OPTARG}
            ;;
        o)
            OUTPUT_DIR=${OPTARG}
            ;;
        g)
            GDB="--gdb"
            ;;
        a)
            GEN_ALIAS=true
            ;;
        \?)
            usage
            ;;
    esac
done

if [[ ${INSTALL_DIR} == "" ]]; then
    echo "-b option must be provided."
    usage
fi

if [[ ${DATA_DIR} == "" ]]; then
    echo "-d option must be provided."
    usage
fi

INSTALL_DIR=`realpath ${INSTALL_DIR}`
DATA_DIR=`realpath ${DATA_DIR}`
OUTPUT_DIR=`realpath ${OUTPUT_DIR}`

if [[ ! -d ${OUTPUT_DIR} ]]; then
    mkdir -p ${OUTPUT_DIR}
fi

if [[ ${GEN_ALIAS} == true ]]; then
    cat > ${OUTPUT_DIR}/pgsql-alias-${PORT}.sh <<EOF
#!/bin/bash

export PATH=${INSTALL_DIR}/bin:\${PATH}
export PGDATA=${DATA_DIR}

alias start.al="pg_ctl start -D ${DATA_DIR} -l ${DATA_DIR}/logfile"
alias ini.al="pg_ctl initdb -D ${DATA_DIR}"
alias proc.al="ps -ef | grep \\\`head -1 ${DATA_DIR}/postmaster.pid\\\` | grep \"postgres\""
alias stop.al="pg_ctl stop -D ${DATA_DIR} -m smart"
alias restart.al="pg_ctl restart -D ${DATA_DIR} -m smart"
alias psql.al="psql -p ${PORT} -d postgres"
alias clean.al="rm -rf ${DATA_DIR}"
alias log.al="less ${DATA_DIR}/logfile"
EOF
fi

echo "Please use following command to update conf file after data directory initialized:"
echo "  sed -e -i 's/#port = 5432/port = ${PORT}/' ${DATA_DIR}/postgresql.conf"
