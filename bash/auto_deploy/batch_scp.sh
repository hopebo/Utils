#!/bin/bash
#
# Batch transfer files to remote servers. Support authenticate automatically.

get_key_value()
{
    echo $1 | sed -E 's/^--?[a-zA-Z_-]*=//'
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
EOF
}

destination=~

while getopts "f:F:h:H:a:d:" opt; do
    case $opt in
        f)
            file=$OPTARG
            ;;
        F)
            file_list=$OPTARG
            ;;
        h)
            host=$OPTARG
            ;;
        H)
            host_list=$OPTARG
            ;;
        a)
            account_file=$OPTARG
            ;;
        d)
            destination=$OPTARG
            ;;
        \?)
            usage
            exit 1
            ;;
    esac
done

if [[ -z ${file} ]]; then
    file=`cat ${file_list} | xargs echo`
fi

if [[ -z ${host} ]]; then
    host=`cat ${host_list}`
fi

if [[ -z ${file} ]] || [[ -z ${host} ]] || [[ -z ${account_file} ]]; then
    echo "Please provide the right options."
    usage
    exit 1
fi

for hostname in ${host}; do
    scp.exp -f "${file}" -h ${hostname} -a ${account_file} \
            -d ${destination}
done
