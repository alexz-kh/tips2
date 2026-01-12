#!/bin/bash -xe

# Duplicate of ubuntu_info.sh
mkdir -p /var/log/bootstrap_logs/ ; pushd /var/log/bootstrap_logs/
  dpkg-query -W -f='${Package}=${Version}\n' |tee -a vcp_initial_pkgs_stage_salt.log
popd

apt-get purge -y salt-formula-*

salt-call saltutil.clear_cache || true

echo "removing all previously accepted salt keys"
salt-key -D -y || true

echo "cleaning up reclass"
rm -rf /srv/salt/reclass || true
rm -rf /srv/salt/scripts || true
rm -rf /usr/share/salt-formulas/env || true
#
mkdir -p /srv/salt/reclass/
mkdir -p /usr/share/salt-formulas/reclass/service/
mkdir -p /usr/share/salt-formulas/env/

# stop and disable services, for healthy zerodisk
# They should be enabled after VCP init
stop_services="salt-minion salt-master salt-api"
for s in ${stop_services} ; do
  systemctl stop ${s} || true
# Enable this, after refactoring salt:control:virtng
#  systemctl disable ${s} || true
done

# remove all keys at all
rm -rf /etc/salt/pki/* || true

# Remove salt-master from apt01
if [[ "$(hostname)" == *"apt01"* ]] ; then
  apt-get purge -y salt-master
  rm -rfv /etc/salt/master.d || true
fi

# remove logs
rm -rf /var/log/salt/* || true

# Clear\drop cache's
sync
echo 3 > /proc/sys/vm/drop_caches
