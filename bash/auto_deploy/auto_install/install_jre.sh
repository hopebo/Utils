#!/bin/bash
#
# Install jre environment from jre*.tar.gz file.

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -e Example, --example Example     Example parameter.
  -s SOURCE_FILE                    jre*.tar.gz file path.
  -d DESTINATION                    Install directory.
  -h, --help                        Print this message and exit.
EOF
}

destination=~/java

while getopts "s:d:h" opt; do
    case $opt in
        s)
            source=$OPTARG
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

if [[ -z ${source} ]]; then
    echo "Please provide the right source file."
    usage
    exit 1
fi

mkdir -p ${destination}
tar -zxvf ${source} -C ${destination}

jre_home=`find ${destination} -name "*jre*"`

cat >> ~/.bashrc <<EOF

# Jre
export JRE_HOME=${jre_home}
export CLASS_PATH=.:\$JRE_HOME/lib
export PATH=\$JRE_HOME/bin:\$PATH
EOF
