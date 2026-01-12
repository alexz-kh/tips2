#!/bin/bash -xe
echo "timeout 10;
backoff-cutoff 0;
initial-interval 0;
retry 15;" >> /etc/dhcp/dhclient.conf
