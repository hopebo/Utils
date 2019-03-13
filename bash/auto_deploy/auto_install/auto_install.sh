#!/bin/bash
#
# Install softwares from resources directory.

echo_green()
{
    echo -e "\033[32m$1\033[0m"
}

echo_red()
{
    echo -e "\033[31m$1\033[0m"
}

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -r RESOURCES_DIR                  Resources directory.
  -j                                Install jre or not.
  -h, --help                        Print this message and exit.
EOF
}

basepath=$(cd `dirname $0`; pwd)

while getopts "r:jd:h" opt; do
    case $opt in
        r)
            resources_dir=$OPTARG
            ;;
        j)
            jre=true
            ;;
        d)
            destination=$OPTARG
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

export PATH=${basepath}:$PATH

if [[ ${jre} = true ]]; then
    jre_tar_gz=`find ${resources_dir} -name "*jre*"`
    if [[ -z ${jre_tar_gz} ]]; then
        echo_red "Please make sure jre.tar.gz in resources directory."
    else
        echo_green "Installing jre environment ..."
        install_jre.sh -s ${jre_tar_gz} -d ${destination}/java
        echo_green "Jre has been installed successfully."
    fi
fi
