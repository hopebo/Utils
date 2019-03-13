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
  -j                                Install jre or not.
EOF
}

basepath=$(cd `dirname $0`; pwd)
destination=~/env
auto_install_options=""

while getopts "h:H:f:F:d:a:j" opt; do
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
        j)
            auto_install_options="${auto_install_options} -j"
            ;;
        \?)
            usage
            exit 1
            ;;
    esac
done

if [[ -z ${host} ]] && [[ ! -z ${host_list} ]]; then
    host=`cat ${host_list} | xargs echo`
fi

if [[ -z ${file} ]] && [[ ! -z ${file_list} ]]; then
    file=`cat ${file_list} | xargs echo`
fi

if [[ -z ${host} ]] || [[ -z ${file} ]] || [[ -z ${account_file} ]]; then
    echo "Please provide the right account file."
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
    # Automatically yum install.
    echo_green "Starting yum installation on ${hostname} ..."
    remote_execution.exp -h ${hostname} -a ${account_file} -l \
                         -c "yum_install.sh"
    echo_green "Yum installation on ${hostname} success."

    # Install using scripts on the remote server.
    echo_green "Starting automatic installation on ${hostname} ..."
    remote_execution.exp -h ${hostname} -a ${account_file} \
                         -c "bash ${destination}/auto_install/auto_install.sh \
                            -r ${destination}/resources -d ${destination} \
                            ${auto_install_options}"
    echo_green "Automatic installation on ${hostname} success."
done
