#!/bin/bash
#
# Generate bash script template.

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -f FILE                   Generated file path.
  -h                        Print this message and exit.

This script is intended to generate bash script template.
EOF
}

if [[ $# = 0 ]]; then
    usage
    exit 0
fi

while getopts "f:h" opt; do
    case $opt in
        f)
            FILE=$OPTARG
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

dump_options()
{
    echo "Dumping the options used by $0 ..."
    echo "FILE=${FILE}"
}

dump_options

cat > ${FILE} <<\CONTENTS
#!/bin/bash
#
# Declare this script's functions and contents.

usage()
{
    cat <<EOF

Usage: $0 [options]

Options:
  -e EXAMPLE                Example paramter.
  -h                        Print this message and exit.

This script is intended to generate bash script template.
EOF
}

BASEPATH=$(cd `dirname $0`; pwd)

while getopts "e:h" opt; do
    case $opt in
        e)
            EXAMPLE=$OPTARG
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
CONTENTS
