#!/bin/bash -xe

# Don't use /tmp/ - some templates do node reboot
if [ -f /done_ubuntu_base ] ; then
  echo "INFO: ubuntu_base already finished.Skipping.."
  exit 0
fi

function prod_21514_wa() {
  echo 'Apply WA for https://mirantis.jira.com/browse/PROD-20751'
  echo 'Installing isc-dhcp from xenial'
  echo "deb [arch=amd64] ${UBUNTU_BASEURL} xenial main restricted universe" > /etc/apt/sources.list.d/xenial.list
  echo "deb [arch=amd64] ${UBUNTU_BASEURL} xenial-updates main restricted universe" >> /etc/apt/sources.list.d/xenial.list
  echo "deb [arch=amd64] ${UBUNTU_BASEURL} xenial-security main restricted universe" >> /etc/apt/sources.list.d/xenial.list
  apt-get update
  apt-get install -y isc-dhcp-client isc-dhcp-common
  rm -v /etc/apt/sources.list.d/xenial.list || true
}

### Body
UBUNTU_BASEURL="${UBUNTU_BASEURL:-mirror://mirrors.ubuntu.com/mirrors.txt}"
## Base packages and setup
export DEBIAN_FRONTEND=noninteractive
echo -e '#!/bin/sh\nexit 101' > /usr/sbin/policy-rc.d
chmod +x /usr/sbin/policy-rc.d

# Configure apt. Please refer to
# https://github.com/Mirantis/reclass-system-salt-model/blob/master/linux/system/single/debian.yml
# and keep those structures with same naming convention - to prevent
# misconfiguration between base system and salt state.
echo "Acquire::CompressionTypes::Order gz;" >/etc/apt/apt.conf.d/99compression-workaround-salt
echo "Acquire::EnableSrvRecords false;" >/etc/apt/apt.conf.d/99enablesrvrecords-false
echo "Acquire::http::Pipeline-Depth 0;" > /etc/apt/apt.conf.d/99aws-s3-mirrors-workaround-salt
echo "APT::Install-Recommends false;" > /etc/apt/apt.conf.d/99dont_install_recommends-salt
echo "APT::Install-Suggests false;" > /etc/apt/apt.conf.d/99dont_install_suggests-salt
echo "Acquire::Languages none;" > /etc/apt/apt.conf.d/99dont_acquire_all_languages-salt
echo "APT::Periodic::Update-Package-Lists 0;" > /etc/apt/apt.conf.d/99dont_update_package_list-salt
echo "APT::Periodic::Download-Upgradeable-Packages 0;" > /etc/apt/apt.conf.d/99dont_update_download_upg_packages-salt
echo "APT::Periodic::Unattended-Upgrade 0;" > /etc/apt/apt.conf.d/99disable_unattended_upgrade-salt

sysctl -w fs.file-max=100000
# Overwrite default mirrors
echo "deb [arch=amd64] ${UBUNTU_BASEURL} trusty main restricted universe" > /etc/apt/sources.list
echo "deb [arch=amd64] ${UBUNTU_BASEURL} trusty-updates main restricted universe" >> /etc/apt/sources.list
echo "deb [arch=amd64] ${UBUNTU_BASEURL} trusty-security main restricted universe" >> /etc/apt/sources.list
prod_21514_wa
apt-get clean
apt-get update

# Useful tools
EXTRA_PKGS="byobu curl ethtool iputils-ping lsof strace tcpdump traceroute wget iptables"
# Pretty tools
EXTRA_PKGS="${EXTRA_PKGS} byobu htop tmux tree vim-nox mc"
# Common prerequisites
EXTRA_PKGS="${EXTRA_PKGS} apt-transport-https libmnl0 python-apt python-m2crypto python-psutil acpid"
apt-get -y install ${EXTRA_PKGS}

# Cleanup old kernels, ensure latest is installed via virtual package
if [ ! -f /tmp/no_install_kernel ]; then
    modprobe cpuid
    apt-get purge -y linux-image-* linux-headers-* | grep -v 'is not installed, so not removed'
    apt-get install -y linux-image-virtual-lts-xenial linux-image-extra-virtual-lts-xenial

    # Update grub cmdline
    sed -i 's|GRUB_CMDLINE_LINUX_DEFAULT=.*|GRUB_CMDLINE_LINUX_DEFAULT="console=tty0 console=ttyS0,115200n8"|g' /etc/default/grub
    sed -i 's|GRUB_CMDLINE_LINUX=.*|GRUB_CMDLINE_LINUX="console=tty0 console=ttyS0,115200n8"|g' /etc/default/grub
    update-grub
fi
apt-get -y upgrade
apt-get -y dist-upgrade

# Tmux fixes
cat << 'EOF' >> /etc/tmux.conf
set -g default-terminal "screen-256color"
set -g set-titles on
set -g xterm-keys on
EOF

# Setup cloud-init
apt-get -y install cloud-init

touch /done_ubuntu_base
