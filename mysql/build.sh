#!/bin/bash
#
# Build MySQL server.

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -t Build Type             debug or release.
  -d Install Directory
  -g                        Enable ASAN.
  -h                        Print this message and exit.

This script is intended to generate bash script template.
EOF
}

WORKPATH=$(pwd)
BASEPATH=$(cd `dirname $0`; pwd)

INSTALL_DIR=/usr/local

while getopts "t:d:gh" opt; do
    case $opt in
        t)
            if [[ ${OPTARG} = "debug" ]]; then
                BUILD_TYPE="Debug"
            else
                BUILD_TYPE="RelWithDebInfo"
            fi
            ;;
        d)
            INSTALL_DIR=${OPTARG}
            ;;
        g)
            ASAN=1
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

# C/CXX common flags
COMMON_FLAGS="-fexceptions -fno-omit-frame-pointer -fno-strict-aliasing -fno-strict-overflow"

if [[ ${BUILD_TYPE} = "Debug" ]]; then
    COMPILE_FLAGS="-O0 -g3 -gdwarf-2"
else
    COMPILE_FLAGS="-O3 -g -gno-as-locview-support"
fi

# CFLAGS: Extra flags to give to the C compiler.
# CXXFLAGS: Extra flags to give to the C++ compiler.
# CPPFLAGS: Extra flags to give to the C preprocessor and programs that use it (the C and Fortran compilers).
export CFLAGS="${COMPILE_FLAGS} ${COMMON_FLAGS}"
export CXXFLAGS="${COMPILE_FLAGS} ${COMMON_FLAGS}"

cmake .. \
  -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
  -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR} \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=1 \
  -DWITH_ASAN=${ASAN} \
  -DWITH_BOOST=../extra
