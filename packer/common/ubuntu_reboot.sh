#!/bin/bash -x

touch /run/is_rebooted
echo 3 > /proc/sys/vm/drop_caches
sync
sleep 1
shutdown -r now
