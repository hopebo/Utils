#!/bin/bash

echo_green()
{
    echo -e "\033[32m$1\033[0m"
}

# Acquire sudo privilege
echo_green "Please input password to acquire sudo privilege ..."
sudo green "Success!"

# Dependencies of R
echo_green "Yum installing dependencies of R ..."
sudo yum install -y readline-devel
sudo yum install -y bzip2-devel
sudo yum install -y libXt-devel
sudo yum install -y xz-devel
sudo yum install -y cairo-devel
sudo yum install -y texlive
sudo yum install -y texinfo
sudo yum install -y curl-devel
sudo yum install -y pcre-devel
echo_green "Successfully install dependencies of R."

# Dependencies of RDS
echo_green "Yum installing dependencies of RDS ..."
sudo yum install -y devtoolset-7* -b current
sudo yum install -y openssl-devel
sudo yum install -y ncurses-devel
sudo yum install -y perl-JSON
sudo yum install -y MySQL-python
sudo yum install -y perl-Time-HiRes
sudo yum install -y perl-Digest-MD5
sudo yum install -y expat-devel
sudo yum install -y gettext-devel
sudo yum install -y zlib-devel
sudo yum install -y asciidoc
sudo yum install -y perl-ExtUtils-MakeMaker
sudo yum install -y bison
sudo yum install -y libasan
sudo yum install -y python-pip
sudo yum install -y llvm-toolset-7-* -b test
cat >> ~/.bashrc <<EOF

# Clang
export PATH=/opt/rh/llvm-toolset-7/root/usr/bin:\$PATH
EOF
echo_green "Successfully install dependencies of RDS."

# Others
echo_green "Yum installing other packages ..."
sudo yum install -y sqlite-devel
sudo yum install -y tk-devel
sudo yum install -y gdbm-devel
sudo yum install -y db4-devel
sudo yum install -y libpcap-devel
sudo yum install -y libffi-devel
echo_green "Successfully install other packages."
