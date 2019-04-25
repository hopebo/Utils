#!/bin/bash
#
# Install software from compressed package.

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -e EXAMPLE                Example paramter.
  -d DESTINATION            Decompress directory.
  -t INSTALL_DIR            Installation dirctory.
  -s SOURCE                 Source file.
  -l                        Export lib or not.
  -h                        Print this message and exit.

This script is intended to install softwares.
EOF
}

BASEPATH=$(cd `dirname $0`; pwd)
DESTINATION=~

while getopts "ls:d:t:k:h" opt; do
    case $opt in
        l)
            EXPORT_LIB=true
            ;;
        s)
            SOURCE=$OPTARG
            ;;
        d)
            DESTINATION=$OPTARG
            ;;
        t)
            INSTALL_DIR=$OPTARG
            ;;
        k)
            KEYWORD=$OPTARG
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

if [[ -z ${SOURCE} ]]; then
    echo "Please provide the right source file."
    usage
    exit 1
fi

mkdir -p ${DESTINATION}
tar -xf ${SOURCE} -C ${DESTINATION}

source_dir=`find ${DESTINATION} -maxdepth 1 -mindepth 1 -name "*${KEYWORD}*"`

output_dir=${source_dir}

if [[ ! -z ${INSTALL_DIR} ]]; then
    mkdir -p ${INSTALL_DIR}
    cd ${source_dir}
    ./configure --prefix=${INSTALL_DIR}
    make -j32 && make install
    output_dir=${INSTALL_DIR}
fi

bin_dir=${output_dir}/bin
lib_dir=${output_dir}/lib

cat >> ~/.bashrc <<EOF

# ${KEYWORD}
export PATH=${bin_dir}:\$PATH
EOF

if [[ ${EXPORT_LIB} = true ]]; then
    cat >> ~/.bashrc <<EOF
export CLASS_PATH=.:${lib_dir}/dt.jar:${lib_dir}/tools.jar
EOF
fi
