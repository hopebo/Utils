#! /bin/bash

function vlog
{
    echo "`date +"%F %T"`: `basename "$0"`: $@" >&1
}

function run_cmd()
{
    vlog "===> $@"
    set +e
    "$@"
    local rc=$?
    set -e
    if [ $rc -ne 0 ]
    then
        die "===> `basename $1` failed with exit code $rc"
    fi
}

function run_cmd_expect_failure()
{
    vlog "===> $@"
    set +e
    "$@"
    local rc=$?
    set -e
    if [ $rc -eq 0 ]
    then
        die "===> `basename $1` succeeded when it was expected to fail"
    fi
}

## These colors can be removed by piping to below sed command
## sed 's/\x1B\[[0-9;]\{1,\}[A-Za-z]//g'
_red() {
    printf '\033[0;31;31m%b\033[0m' "$1"
}

_green() {
    printf '\033[0;31;32m%b\033[0m' "$1"
}

_yellow() {
    printf '\033[0;31;33m%b\033[0m' "$1"
}

_blue() {
    printf '\033[0;31;36m%b\033[0m' "$1"
}

line() {
    printf "%-70s\n" "-" | sed 's/\s/-/g'
}