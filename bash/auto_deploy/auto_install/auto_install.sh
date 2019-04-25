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

find_file_by_key()
{
    dir=$1
    key=$2
    file=`find ${dir} -maxdepth 1 -mindepth 1 -name "*${key}*"`
    if [[ -z ${file} ]]; then
        echo_red "Please make sure ${key} resource file exists."
        exit 1
    fi

    echo ${file}
}

log_start()
{
    echo_green "Installing $1 environment ..."
}

log_end()
{
    echo_green "$1 has been installed successfully."
}

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -r RESOURCES_DIR                  Resources directory.
  -d DESTINATION                    Installation directory.
  -j                                Install jre or not.
  -R                                Install R or not.
  -p                                Add public key or not.
  -l                                Install lcov or not.
  -c                                Install clang+llvm or not.
  -C                                Install cmake or not.
  -v                                Install valgrind or not.
  -h, --help                        Print this message and exit.
EOF
}

basepath=$(cd `dirname $0`; pwd)

while getopts "jRplcCvr:d:h" opt; do
    case $opt in
        r)
            resources_dir=$OPTARG
            ;;
        j)
            jdk=true
            ;;
        d)
            destination=$OPTARG
            ;;
        R)
            R=true
            ;;
        p)
            pub_key=true
            ;;
        l)
            lcov=true
            ;;
        c)
            clang_llvm=true
            ;;
        C)
            cmake=true
            ;;
        v)
            valgrind=true
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

if [[ ${jdk} = true ]]; then
    key="jdk"
    file=$(find_file_by_key ${resources_dir} ${key})
    if [[ -z ${file} ]]; then
        echo_red "Please make sure ${key} resource file exists."
        exit 1
    fi

    log_start ${key}
    general_install.sh -s ${file} -d ${destination} -k ${key} -l
fi

if [[ ${R} = true ]]; then
    key="R"
    file=$(find_file_by_key ${resources_dir} ${key})
    if [[ -z ${file} ]]; then
        echo_red "Please make sure ${key} resource file exists."
        exit 1
    fi

    log_start ${key}
    source ~/.bashrc
    if command -v java >/dev/null 2>&1; then
        general_install.sh -s ${file} -d ${resources_dir}/tmp \
                           -t ${destination}/${key} -k ${key}
    else
        echo_red "R is dependent on Jdk. Please install Jdk first."
    fi
fi

if [[ ${pub_key} = true ]]; then
    key=".pub"
    file=$(find_file_by_key ${resources_dir} ${key})
    if [[ -z ${file} ]]; then
        echo_red "Please make sure ${key} resource file exists."
        exit 1
    fi

    cat ${file} >> ~/.ssh/authorized_keys
fi

if [[ ${lcov} = true ]]; then
    key="lcov"
    file=$(find_file_by_key ${resources_dir} ${key})
    if [[ -z ${file} ]]; then
        echo_red "Please make sure ${key} resource file exists."
        exit 1
    fi

    log_start ${key}
    general_install.sh -s ${file} -d ${destination} -k ${key}
fi

if [[ ${clang_llvm} = true ]]; then
    key="clang"
    file=$(find_file_by_key ${resources_dir} ${key})
    if [[ -z ${file} ]]; then
        echo_red "Please make sure ${key} resource file exists."
        exit 1
    fi

    log_start ${key}
    general_install.sh -s ${file} -d ${destination} -k ${key}
fi

if [[ ${cmake} = true ]]; then
    key="cmake"
    file=$(find_file_by_key ${resources_dir} ${key})
    if [[ -z ${file} ]]; then
        echo_red "Please make sure ${key} resource file exists."
        exit 1
    fi

    log_start ${key}
    general_install.sh -s ${file} -d ${resources_dir}/tmp \
                    -t ${destination}/${key} -k ${key}
fi

if [[ ${valgrind} = true ]]; then
    key="valgrind"
    file=$(find_file_by_key ${resources_dir} ${key})
    if [[ -z ${file} ]]; then
        echo_red "Please make sure ${key} resource file exists."
        exit 1
    fi

    log_start ${key}
    general_install.sh -s ${file} -d ${resources_dir}/tmp \
                    -t ${destination}/${key} -k ${key}
fi

source ~/.bashrc

if [[ ${jdk} = true ]]; then
    if ! command -v java >/dev/null 2>&1; then
        echo_red "Jdk installation failed."
    else
        echo_green "Jdk installation succeeded."
    fi
fi

if [[ ${R} = true ]]; then
    if ! command -v R >/dev/null 2>&1; then
        echo_red "R installation failed."
    else
        echo_green "R installation succeeded."
    fi
fi

if [[ ${lcov} = true ]]; then
    if ! command -v lcov >/dev/null 2>&1; then
        echo_red "Lcov installation failed."
    else
        echo_green "Lcov installation succeeded."
    fi
fi

if [[ ${clang_llvm} = true ]]; then
    if ! command -v clang-format >/dev/null 2>&1; then
        echo_red "Clang installation failed."
    else
        echo_green "Clang installation succeeded."
    fi
fi

if [[ ${cmake} = true ]]; then
    if ! command -v cmake >/dev/null 2>&1; then
        echo_red "Cmake installation failed."
    else
        echo_green "Cmake installation succeeded."
    fi
fi

if [[ ${valgrind} = true ]]; then
    if ! command -v valgrind >/dev/null 2>&1; then
        echo_red "Valgrind installation failed."
    else
        echo_green "Valgrind installation succeeded."
    fi
fi
