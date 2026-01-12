#!/bin/bash
set -x

dd if=/dev/zero of=/EMPTY bs=1M || true
rm -f /EMPTY

for m in $(cat /proc/mounts |grep '/dev/mapper/vg0' | awk '{print $2}'); do
  dd if=/dev/zero of=${m}/EMPTY bs=1M || true
  rm -fv ${m}/EMPTY
done
echo 3 > /proc/sys/vm/drop_caches
sync
