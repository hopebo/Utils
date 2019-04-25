# auto_deploy
Achieve automatically setting up the environment and installing softwares on several remote servers.

## Overview
- auto_deploy.sh: Program entry.
- batch_scp.sh: Batchly copy files to remote servers.
- remote_execute.exp: Execute commands on remote server.
- yum_install.sh: Package installation using `yum install`.
- auto_install: Contains more complex and customized installation scripts like jre.

## Features
- Batchly copy files to remote servers.
- Execute package installation like `yum install` remotely.
- Do more complex and customized installation work remotely. Support expanding the work by plugin.

## Example
```bash
$ ./auto_deploy.sh -H host_list -F file_list -a account -j
```

## Requirements to maximize the functions
- ssh-rsa.pub
- jdk.tar.gz
- R.tar.gz
- lcov.tar.gz
- clang+llvm-linux-gnu.tar.xz
- cmake.tar.gz
- valgrind.tar.bz2
