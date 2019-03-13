# bash
Bash scrpits for automatizing some processes.

## auto_deploy
Achieve automatically setting up the environment and installing softwares on several remote servers.

### Features
- Batchly copy files to remote servers.
- Execute package installation like `yum install` remotely.
- Do more complex and customized installation work remotely. Support expanding the work by plugin.

### Example
```bash
$ ./auto_deploy.sh -h host_list -f file_list -a account -j
```

## gen\_bash_template.sh
Generate a bash script template which can deal with options well.

## setup
Set up bash environment including alias, LS_COLORS and variables.

## ssh
Automatically ssh the remote server.
