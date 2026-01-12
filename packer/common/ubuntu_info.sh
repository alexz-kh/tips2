#!/bin/bash -xe

# Save some basic debug information.

mkdir -p /var/log/bootstrap_logs/ ; pushd /var/log/bootstrap_logs/
  dpkg-query -W -f='${Package}=${Version}\n' | sort -u |tee -a vcp_initial_pkgs.log
popd
