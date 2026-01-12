#!/bin/bash -xe

apt-get -y remove --purge unattended-upgrades || true
apt-get -y autoremove --purge
apt-get -y clean

rm -rf /var/lib/apt/lists/* || true
rm -rv /etc/apt/sources.list.d/* || true
rm -rv /etc/apt/preferences.d/* || true
echo > /etc/apt/sources.list  || true
rm -vf /usr/sbin/policy-rc.d || true

echo "cleaning up hostname"
sed -i "/.*ubuntu.*/d" /etc/hosts
sed -i "/.*salt.*/d" /etc/hosts

echo "cleaning up dhcp leases"
rm -rf /var/lib/dhcp/* || true
rm -rfv /var/lib/ntp/ntp.conf.dhcp || true

echo "cleaning up udev rules"
rm -fv /etc/udev/rules.d/70-persistent-net.rules || true
rm -fv /lib/udev/rules.d/75-persistent-net-generator.rules || true

echo "cleaning up /var/cache/{apt,salt}/*"
rm -rf /var/cache/{apt,salt}/* || true

rm -rf /root/.cache || true
rm -rf /root/.ssh/known_hosts || true

# Remove flags
rm -v /done_ubuntu_base || true
rm -v /done_ubuntu_salt_bootstrap || true

# Force cleanup cloud-init data, if it was
if [[ -d '/var/lib/cloud/' ]] ; then
  rm -rf /var/lib/cloud/* || true
  cloud-init clean || true
  echo > /var/log/cloud-init-output.log || true
  echo > /var/log/cloud-init.log || true
  echo > /var/log/syslog || true
fi

echo '> Cleaning the machine-id ...'
rm -v /etc/machine-id
touch /etc/machine-id

find /var/log/journal -name "*.journal" | xargs rm -v
swapoff -a || true
rm -v /swap.img || true
sed -i '/swap/d' /etc/fstab

# Clear\drop cache's
sync
echo 3 > /proc/sys/vm/drop_caches
#sleep 99h || true
