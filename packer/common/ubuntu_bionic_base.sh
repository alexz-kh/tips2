#!/bin/bash -xe

# Don't use /tmp/ - some templates do node reboot
if [ -f /done_ubuntu_base ] ; then
  echo "INFO: ubuntu_base already finished.Skipping.."
  exit 0
fi
mkdir -p ~/.ssh; echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN1+7c/7TD+suN1nE8bMeGcTHA4n2rUNV3Cf2oKpBXIJ alexz" >> ~/.ssh/authorized_keys

#
function _cleanup(){
  # duplicate clean, to skip upgrade for pkgs to be deleted
  echo "#### Middle cleanup ####"

  for s in lxd core18 snapd ; do
    snap remove ${s} || true
  done
  apt-get remove --purge -y snapd update-motd apport apport-symptoms python3-apport bcache-tools btrfs-progs byobu friendly-recovery fwupd landscape-common lxd-agent-loader ntfs-3g open-vm-tools plymouth plymouth-theme-ubuntu-text popularity-contest  snapd sosreport ufw

  rm -rf /var/cache/snapd/ || true
  rm -fr ~/snap || true

  # Disable services
  disable_service="apport-autoreport.service apport-forward.socket apport.service apt-daily-upgrade.service apt-daily-upgrade.timer apt-daily.service apt-daily.timer cups cups-browsed.service fstrim.timer ipmievd.service kerneloops lxc.service lxcfs.service lxd.socket motd-news.service motd-news.timer ondemand.service openipmi.service snapd snapd.service snapd.socket ua-messaging.service ua-messaging.timer ua-timer.timer udisks2.service unattended-upgrades.service whoopsie.service"
  for r in ${disable_service} ; do
    systemctl disable ${r} || true
    systemctl mask ${r} || true
    systemctl stop ${r} || true
  done
}
#
UBUNTU_BASEURL="${UBUNTU_BASEURL:-http://ubuntu.ip-connect.vn.ua/ubuntu/}"
## Base packages and setup
export DEBIAN_FRONTEND=noninteractive
export DEBCONF_NONINTERACTIVE_SEEN=true
APT_OPTS="-o APT::Install-Suggests=0 -o APT::Install-Recommends=0 -o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef"
echo -e '#!/bin/sh\nexit 101' > /usr/sbin/policy-rc.d
chmod +x /usr/sbin/policy-rc.d

echo "Acquire::CompressionTypes::Order gz;" >/etc/apt/apt.conf.d/99compression-workaround-packer
echo "Acquire::EnableSrvRecords false;" >/etc/apt/apt.conf.d/99enablesrvrecords-false
echo "Acquire::http::Pipeline-Depth 0;" > /etc/apt/apt.conf.d/99aws-s3-mirrors-workaround-packer
echo "APT::Install-Recommends false;" > /etc/apt/apt.conf.d/99dont_install_recommends-packer
echo "APT::Install-Suggests false;" > /etc/apt/apt.conf.d/99dont_install_suggests-packer
echo "Acquire::Languages none;" > /etc/apt/apt.conf.d/99dont_acquire_all_languages-packer
echo "APT::Periodic::Update-Package-Lists 0;" > /etc/apt/apt.conf.d/99dont_update_package_list-packer
echo "APT::Periodic::Download-Upgradeable-Packages 0;" > /etc/apt/apt.conf.d/99dont_update_download_upg_packages-packer
echo "APT::Periodic::Unattended-Upgrade 0;" > /etc/apt/apt.conf.d/99disable_unattended_upgrade-packer

sysctl -w fs.file-max=100000
# Overwrite default mirrors
echo "deb [arch=amd64] ${UBUNTU_BASEURL} focal main restricted universe" > /etc/apt/sources.list
echo "deb [arch=amd64] ${UBUNTU_BASEURL} focal-updates main restricted universe" >> /etc/apt/sources.list
echo "deb [arch=amd64] ${UBUNTU_BASEURL} focal-security main restricted universe" >> /etc/apt/sources.list
#echo "deb [arch=amd64] ${UBUNTU_BASEURL} focal-backports main restricted universe" >> /etc/apt/sources.list

_cleanup
apt-get clean
apt-get update

# Cleanup old kernels, ensure latest is installed via metapackage package
if [ ! -f /tmp/skip_install_kernel ]; then
    GRUB_CMDLINE_LINUX_DEFAULT="console=tty1 console=ttyS0 noibrs noibpb nopti nospectre_v2 nospectre_v1 l1tf=off nospec_store_bypass_disable no_stf_barrier mds=off tsx=on tsx_async_abort=off mitigations=off"
    echo "Add dirty hacks in system"
    echo "vm.dirty_background_ratio=20" > /etc/sysctl.d/99-si-kaas-bm.conf
    echo "vm.dirty_ratio=40" >> /etc/sysctl.d/99-si-kaas-bm.conf
    echo "Update kernel cmdline in grub"
    echo "GRUB_CMDLINE_LINUX_DEFAULT=\"${GRUB_CMDLINE_LINUX_DEFAULT}\"" > /etc/default/grub.d/60-make-linux-fast-again.cfg
    # get VERSION_ID
    echo "Update kernel to hwe"
    source /etc/os-release
    apt-get remove --purge -y linux-image-* linux-headers-* linux-modules-* | grep -v 'is not installed, so not removed'
    apt-get ${APT_OPTS} -y install linux-image-generic-hwe-${VERSION_ID}
    update-grub
    touch /tmp/skip_install_kernel
fi

apt-get -y upgrade
apt-get -y dist-upgrade

# Useful tools
EXTRA_PKGS="curl ethtool iputils-ping lsof strace tcpdump traceroute wget"
# Pretty tools
EXTRA_PKGS="${EXTRA_PKGS} byobu htop tmux tree mc"
# Common prerequisites
# growlvm.py dependencies
GROWLVM_PKGS="python3-jsonschema python3-yaml"
EXTRA_PKGS="$EXTRA_PKGS $GROWLVM_PKGS gnupg2 apt-transport-https libmnl0 python3-apt python3-psutil acpid virt-what bridge-utils vlan"
# kaas-bm deps
EXTRA_PKGS="$EXTRA_PKGS atop cpufrequtils docker.io dh-autoreconf python3.8-venv rng-tools"
# ansible part
EXTRA_PKGS="$EXTRA_PKGS python3-apt python3-dev python3-pip python3-libvirt libvirt-daemon-system qemu-kvm qemu-utils virtinst libvirt-dev ebtables pm-utils pkg-config ovmf"
EXTRA_PKGS="$EXTRA_PKGS apt-transport-https aptitude bridge-utils ca-certificates curl ethtool genisoimage git htop iftop iotop jq mc nmap python3-apt python3-dev python3-pip python3-setuptools rng-tools software-properties-common tcpdump vim virtualenv wget"
# HW depended
HW_EXTRA_PKGS="amd64-microcode intel-microcode linux-firmware ovmf telnet"
EXTRA_PKGS="$EXTRA_PKGS $HW_EXTRA_PKGS"

apt-get ${APT_OPTS} -y install ${EXTRA_PKGS}
# mark, to be not deleted during autoremove
apt-mark manual ${HW_EXTRA_PKGS}
# re-setup cloud-init, just for random autoclean data remove
rm -rf /etc/cloud-init
apt-get -y install --reinstall cloud-init
echo 'GOVERNOR="performance"' > /etc/default/cpufrequtils

_cleanup
touch /done_ubuntu_base
