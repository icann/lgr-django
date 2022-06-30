#!/bin/sh

# A simple container to host a redis server

# Criticaly exit script if one command in error
set -e

printf "\tInstall Redis\t"
# Install compilation tools for django and icu4c
dnf -qy install redis

printf "OK\n"

printf "\tClean up dnf cache files\t"
dnf -qy clean all
rm -fr /var/cache/dnf
printf "OK\n"
