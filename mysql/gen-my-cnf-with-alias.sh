#!/bin/bash

usage() {
    echo "usage: gen-my-cnf.sh [-ag] [-b install_dir] [-d data_dir]"
    echo "  [-p port] [-o output_dir]"
    echo ""
    echo " b - mysql installation directory"
    echo " d - mysql data directory"
    echo " p - port number the server listens on"
    echo " o - generated files saving directory"
    echo " g - start mysqld with gdb"
    echo " a - generate mysql alias file"
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

if [[ ${PORT} == "" ]]; then
    echo "-p option must be provided."
    usage
fi

if [[ ! -d ${OUTPUT_DIR} ]]; then
    mkdir -p ${OUTPUT_DIR}
fi

INSTALL_DIR=`realpath ${INSTALL_DIR}`
DATA_DIR=`realpath ${DATA_DIR}`
OUTPUT_DIR=`realpath ${OUTPUT_DIR}`
MY_CNF=${OUTPUT_DIR}/my-${PORT}.cnf

cat > ${MY_CNF} <<EOF
[mysqld]
# Do not listen for TCP/IP connections at all. All interactions with mysqld must be made using named pipes (Windows) or Unix socket files (on Unix).
# This option is highly recommended for systems where only local clients are permitted.
skip-networking
# Disable (default) external locking (system locking). External locking will cause it easy for mysqld to deadlock on a system on which lockd does not fully work (such as Linux).
skip-external-locking
# Limit effect of import and export operations. Valid values: empty string, dirname, NULL.
# If empty: the variable has no effect. This is not a secure setting.
# If set to the name of a directory: the server limits import and export operations to work only with files in that directory. The directory must exist.
# If set to NULL: the server disables import and export operations.
# The default value is platform specific and depends on the value of the INSTALL_LAYOUT CMake option.
secure-file-priv                = ""
# Storage engine for permanent tables only. Default: InnoDB
default-storage-engine          = InnoDB
# The path name of the process ID file. The server creates the file in the data directory unless an absolute path name is given to specify a different directory. The default value of file name is host_name.pid.
pid-file                        = ${DATA_DIR}/mysql.pid
# On Unix, this option specifies the Unix socket file to use when listening for local connections. The default value is /tmp/mysql.sock.
socket                          = ${DATA_DIR}/mysql.sock
# Address on which the MySQL server listens on.
# *: accepts TCP/IP connections on all server host IPv4 and IPv6 interfaces.
# 0.0.0.0: accepts all IPv4 interfaces.
# "::": same as *.
# A list of comma-seperated values.
bind-address                   = 0.0.0.0
# The path to the MySQL server data directory.
datadir                        = ${DATA_DIR}
# The path to the MySQL installation directory. The server executable determines its own full path name using the parent of the directory in which it is located as the default value.
# This in turn enables the server to use that basedir when searching for server-related information such as the share directory containing error messages.
basedir                        = ${INSTALL_DIR}
# Set the default error log destination to the named file.
log-error                      = ${DATA_DIR}/mysql_error.log
# Limits the total number of prepared statements in the server. It can be used in environments where there is the potential for denial-of service attacks based on running the server out of memory by preparing huge numbers of statements.
# Default: 16382 Minimum: 0 Maximum: 1048576
# Prepared statement supports placeholder. MySQL can compile the prepared statement with placeholder in advance. Then we can use variable to replace the placeholder and just run, which can accelerate the execution.
max_prepared_stmt_count        = 1048576
# The maximum permitted number of simultaneous client connections.
# Default: 151 Minimum: 1 Maximum: 100000
max_connections                = 1000
# The number of the port on which the server listens for TCP/IP connections.
port                           = ${PORT}

[mysqld_safe]
# Passed to mysqld_safe process to communicate with mysqld process.
socket                         = ${DATA_DIR}/mysql.sock
EOF

sed -i "/#.*/d" ${MY_CNF}

if [[ ${GEN_ALIAS} == true ]]; then
    cat > ${OUTPUT_DIR}/mysql-alias-${PORT}.sh <<EOF
#!/bin/bash

export PATH=${INSTALL_DIR}/bin:${PATH}

alias mysqld_safe.al="mysqld_safe --defaults-file=${MY_CNF} ${GDB} > /dev/null 2>&1 &"
alias ini.al="mysqld --defaults-file=${MY_CNF} --initialize-insecure"
alias proc.al="ps -ef | grep \"mysqld\" | grep \"${MY_CNF}\""
alias kill.al="ps -ef | grep \"mysqld\" | grep \"${MY_CNF}\" | awk '{ print \\\$2 }' | xargs kill -9"
alias mysql.al="mysql -u root --socket=${DATA_DIR}/mysql.sock --prompt \"\\u@\\h:\\d \\v>\\_\""
alias clean.al="rm -rf ${DATA_DIR}"
alias cnf.al="vim ${MY_CNF}"
alias log.al="vim ${DATA_DIR}/mysql_error.log"
EOF
fi
