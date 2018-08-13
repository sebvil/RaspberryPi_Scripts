#!/bin/bash


str=$(avahi-resolve-host-name sebastian-VirtualBox.local)
read -ra ADDR <<< "$str"
echo ${ADDR[1]}%eth0

