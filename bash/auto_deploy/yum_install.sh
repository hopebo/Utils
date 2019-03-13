#!/bin/bash

echo_green()
{
    echo -e "\033[32m$1\033[0m"
}

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
echo_green "Successfully install dependencies of R."
