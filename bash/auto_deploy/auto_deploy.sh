#!/bin/bash
#
# Deploy environment in remote servers.
# Support automatic pakage installation and manual script installation.

echo_green()
{
    echo -e "\033[32m$1\033[0m"
}

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -h HOST                           Target host ip or hostname.
  -H HOST_LIST                      File which contains a hostname each row.
  -f FILE                           Resource filename to transfer.
  -F FILE_LIST                      File which contains resource file each row.
  -d DESTINATION                    Directory in remote server to deploy as the base path.
  -a ACCOUNT_FILE                   File which contains username and password in two rows to authenticate.
  -s COMMANDS_SCRIPT                Script file which contains commands to execute on remote server.
  -j                                Install jre or not.
  -R                                Install R or not.
  -p                                Add public key or not.
  -l                                Install lcov or not.
  -c                                Install clang+llvm or not.
  -C                                Install cmake or not.
  -v                                Install valgrind or not.
EOF
}

basepath=$(cd `dirname $0`; pwd)
destination=~/env
auto_install_options=""

while getopts "jpRlcCvh:H:f:F:d:a:s:" opt; do
    case $opt in
        h)
            host=$OPTARG
            ;;
        H)
            host_list=$OPTARG
            ;;
        f)
            file=$OPTARG
            ;;
        F)
            file_list=$OPTARG
            ;;
        d)
            destination=$OPTARG
            ;;
        a)
            account_file=$OPTARG
            ;;
        s)
            commands_script=$OPTARG
            ;;
        j)
            auto_install_options="${auto_install_options} -j"
            ;;
        p)
            auto_install_options="${auto_install_options} -p"
            ;;
        R)
            auto_install_options="${auto_install_options} -R"
            ;;
        l)
            auto_install_options="${auto_install_options} -l"
            ;;
        c)
            auto_install_options="${auto_install_options} -c"
            ;;
        C)
            auto_install_options="${auto_install_options} -C"
            ;;
        v)
            auto_install_options="${auto_install_options} -v"
            ;;
        \?)
            usage
            exit 1
            ;;
    esac
done

if [[ -z ${host} ]] && [[ ! -z ${host_list} ]]; then
    hosts=`cat ${host_list} | xargs echo`
    for hostname in ${hosts}; do
        if [[ ${hostname} != \#* ]]; then
            host="${host} ${hostname}"
        fi
    done
fi

if [[ -z ${file} ]] && [[ ! -z ${file_list} ]]; then
    files=`cat ${file_list} | xargs echo`
    for filename in ${files}; do
        if [[ ${filename} != \#* ]]; then
            file="${file} ${filename}"
        fi
    done
fi

if [[ -z ${host} ]] || [[ -z ${file} ]] || [[ -z ${account_file} ]]; then
    echo "Please provide the right account file."
    exit 1
fi

if ! command -v expect >/dev/null 2>&1; then
    echo "Please install expect firstly."
    exit 1
fi

export PATH=${basepath}:$PATH

# Scp resources to remote servers.
echo_green "Transferring resource files to ${host} ..."
batch_scp.sh -f "${file}" -h "${host}" -d ${destination}/resources \
             -a ${account_file}
echo_green "Resources transfer to ${host} successfully."

# Scp installation scripts to remote servers.
echo_green "Transferring utilities to ${host} ..."
batch_scp.sh -f ${basepath}/auto_install -h "${host}" -d ${destination} \
             -a ${account_file}
echo_green "Utilities transfer to ${host} successfully."

for hostname in ${host}; do
    if [[ ${hostname} = \#* ]]; then
        continue
    fi

    if [[ ! -z ${commands_script} ]]; then
        # Execute commands on remote servers.
        echo_green "Starting executing commands on ${hostname} ..."
        remote_execution.exp -h ${hostname} -a ${account_file} -l \
                             -c "${commands_script}"
        echo_green "Executing commands on ${hostname} success."
    fi

    # Install using scripts on the remote server.
    echo_green "Starting automatic installation on ${hostname} ..."
    remote_execution.exp -h ${hostname} -a ${account_file} \
                         -c "bash ${destination}/auto_install/auto_install.sh \
                            -r ${destination}/resources -d ${destination} \
                            ${auto_install_options}"
    echo_green "Automatic installation on ${hostname} success."

    # Clear up workspace on the remote server.
    echo_green "Clearing up workspace on ${hostname} ..."
    remote_execution.exp -h ${hostname} -a ${account_file} \
                         -c "rm -rf ${destination}/resources \
                            ${destination}/auto_install"
    echo_green "Workspace clearing up on ${hostname} success."
done
