#!/bin/bash -xe

if [ -f '/done_ubuntu_salt_bootstrap' ]; then
  echo "INFO: ubuntu_salt_bootstrap already finished! Skipping.."
  exit 0
fi
#
CLUSTER_NAME=${CLUSTER_NAME:-lost_cluster_name_variable}
MCP_VERSION=${MCP_VERSION:-testing}
SALTSTACK_GPG=${SALTSTACK_GPG:-"http://mirror.mirantis.com/${MCP_VERSION}/saltstack-2017.7/xenial/SALTSTACK-GPG-KEY.pub"}
SALTSTACK_REPO=${SALTSTACK_REPO:-"http://mirror.mirantis.com/${MCP_VERSION}/saltstack-2017.7/ xenial main"}
APT_MIRANTIS_SALT_GPG=${APT_MIRANTIS_SALT_GPG:-"http://mirror.mirantis.com/${MCP_VERSION}/salt-formulas/xenial/archive-salt-formulas.key"}
APT_MIRANTIS_SALT_REPO=${APT_MIRANTIS_SALT_REPO:-"deb [arch=amd64] http://mirror.mirantis.com/${MCP_VERSION}/salt-formulas/xenial xenial main"}

function process_repos(){
# TODO: those  should be unhardcoded and re-writed, using CC model
wget -O - ${SALTSTACK_GPG} | sudo apt-key add -
wget -O - ${APT_MIRANTIS_SALT_GPG} | apt-key add -
wget -O - http://mirror.mirantis.com/${MCP_VERSION}/extra/xenial/archive-extra.key | apt-key add -

echo "deb [arch=amd64] ${SALTSTACK_REPO}"  > /etc/apt/sources.list.d/mcp_saltstack.list
echo "deb [arch=amd64] http://mirror.mirantis.com/${MCP_VERSION}/extra/xenial xenial main"  > /etc/apt/sources.list.d/mcp_extra.list

# This Pin-Priority fix should be always aligned with
# https://github.com/Mirantis/reclass-system-salt-model/blob/master/linux/system/repo/mcp/apt_mirantis/saltstack.yml
# saltstack
cat <<EOF >> /etc/apt/preferences.d/mcp_saltstack
Package: libsodium18
Pin: release o=SaltStack
Pin-Priority: 50

Package: *
Pin: release o=SaltStack
Pin-Priority: 1100
EOF
# reclass
cat <<EOF >> /etc/apt/preferences.d/mcp_extra
Package: *
Pin: release o=Mirantis
Pin-Priority: 1100
EOF
}

process_repos
apt-get update
apt-get install git-core reclass -y

rm -v /etc/apt/sources.list.d/mcp_extra.list /etc/apt/preferences.d/mcp_extra

[ ! -d /srv/salt ] && mkdir -p /srv/salt
mount /dev/cdrom /mnt
if [[ ! -d /srv/salt/reclass ]]; then
  cp -r /mnt/model /srv/salt/reclass
fi

if [[ ! -d /srv/salt/scripts ]]; then
  cp -r /mnt/salt_scripts /srv/salt/scripts
fi
umount /mnt

# bootstrap.sh opts
export FORMULAS_SOURCE=pkg
export HOSTNAME=${BS_HOSTNAME:-lost_bs_hostname_variable}
export DOMAIN="${CLUSTER_NAME}.local"
export EXTRA_FORMULAS=${EXTRA_FORMULAS:-"aptly docker gerrit git iptables jenkins keycloak logrotate maas ntp nginx openldap sphinx"}
export APT_REPOSITORY=" deb [arch=amd64] ${APT_MIRANTIS_SALT_REPO} "
export APT_REPOSITORY_GPG=${APT_MIRANTIS_SALT_GPG}
export SALT_STOPSTART_WAIT=${SALT_STOPSTART_WAIT:-10}
echo "INFO: build in offline build!"
export BOOTSTRAP_SALTSTACK_COM=${BOOTSTRAP_SALTSTACK_COM:-"file:///tmp/bootstrap.saltstack.com.sh"}
# extra opts will push bootstrap script NOT install upstream repos.
export BOOTSTRAP_SALTSTACK_OPTS=${BOOTSTRAP_SALTSTACK_OPTS:- -dXr $BOOTSTRAP_SALTSTACK_VERSION }
#

if [[ ! -f /srv/salt/scripts/bootstrap.sh ]]; then
  echo "ERROR: File /srv/salt/scripts/bootstrap.sh not found"
  exit 1
fi
bash -x /srv/salt/scripts/bootstrap.sh || true
touch /done_ubuntu_salt_bootstrap
