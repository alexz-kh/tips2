#!/bin/bash
# Copy-paste from
# https://github.com/openstack/fuel-main/blob/7.0-eol/fuel-bootstrap-image-builder/bin/fuel-bootstrap-image
set -ex
MYSELF="${0##*/}"

bindir="${0%/*}"
datadir="${bindir%/*}/share/"

global_conf="/etc/fuel-bootstrap-image.conf"
[ -r "$global_conf" ] && . "$global_conf"

[ -z "$MOS_VERSION" ] && MOS_VERSION="7.0"
[ -z "$DISTRO_RELEASE" ] && DISTRO_RELEASE="xenial"
[ -z "$MIRROR_DISTRO" ] && MIRROR_DISTRO="http://ua.archive.ubuntu.com/ubuntu"
[ -z "$ARCH" ] && ARCH="amd64"
[ -z "$DESTDIR" ] && DESTDIR="rez_ubuntu"
mkdir -p $DESTDIR
LINUX_KERNEL=linux-image-generic-hwe-16.04-edge

# Packages required for the master node to discover a bootstrap node
BOOTSTRAP_FUEL_PKGS_DFLT="openssh-client openssh-server ntp"
[ -z "$BOOTSTRAP_FUEL_PKGS" ] && BOOTSTRAP_FUEL_PKGS="$BOOTSTRAP_FUEL_PKGS_DFLT"

if [ -n "$http_proxy" ]; then
	export HTTP_PROXY="$http_proxy"
elif [ -n "$HTTP_PROXY" ]; then
	export http_proxy="$HTTP_PROXY"
fi

# Kernel, firmware, live boot
BOOTSTRAP_PKGS="ubuntu-minimal live-boot live-boot-initramfs-tools ${LINUX_KERNEL} linux-firmware"
# compress initramfs with xz, make squashfs root filesystem image
BOOTSTRAP_PKGS="$BOOTSTRAP_PKGS xz-utils squashfs-tools"
# Smaller tools providing the standard ones.
# - mdadm depends on mail-transport-agent, default one is postfix => use msmtp instead
BOOTSTRAP_PKGS="$BOOTSTRAP_PKGS msmtp-mta"
# Other
BOOTSTRAP_PKGS="$BOOTSTRAP_PKGS lshw tcpdump hwloc mc tcpdump vim wget strace iotop htop iftop lvm2 parted gdisk util-linux dmidecode"

apt_setup ()
{
	local root="$1"
	local sources_list="${root}/etc/apt/sources.list"
	local apt_prefs="${root}/etc/apt/preferences"
  local apt_conf="${root}/etc/apt/apt.conf.d/99alexz"
  mkdir -p ${root}/etc/apt/apt.conf.d/
	mkdir -p "${sources_list%/*}"

	cat > "$sources_list" <<-EOF
	deb [arch=amd64] $MIRROR_DISTRO ${DISTRO_RELEASE}         main universe multiverse restricted
	deb [arch=amd64] $MIRROR_DISTRO ${DISTRO_RELEASE}-security main universe multiverse restricted
	deb [arch=amd64] $MIRROR_DISTRO ${DISTRO_RELEASE}-updates  main universe multiverse restricted
	EOF

	cat > "$apt_conf" <<-EOF
	Acquire::CompressionTypes::Order gz;
	Acquire::EnableSrvRecords false;
	Acquire::http::Pipeline-Depth 0;
	APT::Install-Recommends false;
	APT::Install-Suggests false;
	Acquire::Languages none;
	APT::Periodic::Update-Package-Lists 0;
	APT::Periodic::Download-Upgradeable-Packages 0;
	APT::Get::AllowUnauthenticated 1;
	APT::Periodic::Unattended-Upgrade 0;
	EOF

	if [ -n "$HTTP_PROXY" ]; then
		cat > "$root/etc/apt/apt.conf.d/01use-proxy" <<-EOF
		Acquire::http::Proxy "$HTTP_PROXY";
		EOF
	fi
}

run_apt_get ()
{
	local root="$1"
	shift
	chroot "$root" env \
		LC_ALL=C \
		DEBIAN_FRONTEND=noninteractive \
		DEBCONF_NONINTERACTIVE_SEEN=true \
		TMPDIR=/tmp \
		TMP=/tmp \
		apt-get $@
}

run_debootstrap ()
{
	local root="$1"
	[ -z "$root" ] && exit 1
	local insecure="--no-check-gpg"
	local extractor=''
	env \
		LC_ALL=C \
		DEBIAN_FRONTEND=noninteractive \
		DEBCONF_NONINTERACTIVE_SEEN=true \
		debootstrap $insecure $extractor --arch=${ARCH} ${DISTRO_RELEASE} "$root" $MIRROR_DISTRO
}

install_packages ()
{
	local root="$1"
	shift
	echo "INFO: $MYSELF: installing pkgs: $*" >&2
	run_apt_get "$root" install --yes $@
}

upgrade_chroot ()
{
	local root="$1"
	run_apt_get "$root" update
	if ! mountpoint -q "$root/proc"; then
		mount -t proc bootstrapproc "$root/proc"
	fi
	run_apt_get "$root" upgrade --yes
}

suppress_services_start ()
{
	local root="$1"
	local policy_rc="$root/usr/sbin/policy-rc.d"
	mkdir -p "${policy_rc%/*}"
	cat > "$policy_rc" <<-EOF
	#!/bin/sh
	# suppress services start in the staging chroot
	exit 101
	EOF
	chmod 755 "$policy_rc"
}

propagate_host_resolv_conf ()
{
	local root="$1"
	mkdir -p "$root/etc"
	for conf in "/etc/resolv.conf" "/etc/hosts"; do
		if [ -e "${root}${conf}" ]; then
			cp -a "${root}${conf}" "${root}${conf}.bak"
		fi
	done
}

restore_resolv_conf ()
{
	local root="$1"
	for conf in "/etc/resolv.conf" "/etc/hosts"; do
		if [ -e "${root}${conf}.bak" ]; then
			rm -f "${root}${conf}"
			cp -a "${root}${conf}.bak" "${root}${conf}"
		fi
	done
}

make_utf8_locale ()
{
	local root="$1"
	chroot "$root" /bin/sh -c "locale-gen en_US.UTF-8 && dpkg-reconfigure locales"
}

copy_conf_files ()
{
	local root="$1"
	rsync -rvlptDK "$datadir/${DISTRO_RELEASE}/files/" "${root%/}"
	sed -i $root/etc/shadow -e '/^root/c\root:$6$oC7haQNQ$LtVf6AI.QKn9Jb89r83PtQN9fBqpHT9bAFLzy.YVxTLiFgsoqlPY3awKvbuSgtxYHx4RUcpUqMotp.WZ0Hwoj.:15441:0:99999:7:::'
  mkdir -p $root/root/.ssh/
  echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGmNI+xV2sgIZX6tr5i4eQcxM4rkNoMiFbUuxtZYw5rKci9cSp9C/NC11VnJzpLG3lf11vLwTztlaM7hjdYlKoynpfDhfRhg1p5w/Pd/uoh6bO7KP/r2QuSpVsc6NGAHD2f0qxmrFX81xMG6zq0MCHXc+BGMZTKWAW7dMGsjJUnIa/wv24J25DOILoEBhclGQHx5r7R5ysqSOTdBEgN304KL8XPP+bAwDFTNJIwtfBdNt8jSv6yR2CyfB7t8pqXf93DvwaGBJfuu1r4gljj5ozCyvGExEtRTzvAC+oLq2NIfDOCC3iRWXrls3iDLZYxwm7VLcQSre4Yp6jfp+WuRI7 alexz" >> ${root}/root/.ssh/authorized_keys
  sed -i 's/PermitRootLogin.*/PermitRootLogin yes/g' ${root}/etc/ssh/sshd_config
  sed -i 's/PasswordAuthentication.*/PasswordAuthentication yes/g' ${root}/etc/ssh/sshd_config
  chmod 640 ${root}/root/.ssh/authorized_keys
}

cleanup_chroot ()
{
	local root="$1"
	[ -z "$root" ] && exit 1
  run_apt_get ${root} clean
	signal_chrooted_processes "$root" SIGTERM
	signal_chrooted_processes "$root" SIGKILL
	umount "${root}/tmp/local-apt" 2>/dev/null || umount -l "${root}/tmp/local-apt" || true
	rm -f "${root}/etc/apt/sources.list.d/nailgun-local.list"
	rm -rf $root/var/cache/apt/archives/*.deb
	rm -f $root/var/log/bootstrap.log
	rm -rf $root/tmp/*
	rm -rf $root/run/*
}

recompress_initramfs ()
{
	local root="$1"
	local initramfs_conf="$root/etc/initramfs-tools/initramfs.conf"
	sed -i $initramfs_conf -re 's/COMPRESS\s*=\s*gzip/COMPRESS=xz/'
	rm -fv $root/boot/initrd*
	chroot "$root" \
		env \
		LC_ALL=C \
		DEBIAN_FRONTEND=noninteractive \
		DEBCONF_NONINTERACTIVE_SEEN=true \
		TMPDIR=/tmp \
		TMP=/tmp \
		update-initramfs -c -k all
}

mk_squashfs_image ()
{
	local root="$1"
	local tmp="$$"
	[ -d "$DESTDIR" ] && mkdir -p "$DESTDIR"
	cp -av $root/boot/initrd* $DESTDIR/initramfs.img.${tmp}
	cp -av $root/boot/vmlinuz* $DESTDIR/linux.${tmp}
	rm -fv $root/boot/initrd*
	rm -fv $root/boot/vmlinuz*

	# run mksquashfs inside a chroot (Ubuntu kernel will be able to
	# mount an image produced by Ubuntu squashfs-tools)
	mount -t tmpfs -o rw,nodev,nosuid,noatime,mode=0755,size=4M mnt${tmp} "$root/mnt"
	mkdir -p "$root/mnt/src" "$root/mnt/dst"
	mount -o bind "$root" "$root/mnt/src"
	mount -o remount,bind,ro "$root/mnt/src"
	mount -o bind "$DESTDIR" "$root/mnt/dst"

	if ! mountpoint -q "$root/proc"; then
		mount -t proc sandboxproc "$root/proc"
	fi
	chroot "$root" mksquashfs /mnt/src /mnt/dst/root.squashfs.${tmp} -comp xz -no-progress -noappend
	mv $DESTDIR/initramfs.img.${tmp} $DESTDIR/initramfs.img
	mv $DESTDIR/linux.${tmp} $DESTDIR/linux
	mv $DESTDIR/root.squashfs.${tmp} $DESTDIR/root.squashfs

	umount "$root/mnt/dst"
	umount "$root/mnt/src"
	umount "$root/mnt"
}

build_image ()
{
	local root="$1"
	chmod 755 "$root"
	suppress_services_start "$root"
	run_debootstrap "$root"
	# copy rules for Predictable Network Interface Names
	#cp "$datadir/${DISTRO_RELEASE}/files/lib/udev/rules.d/80-net-name-slot.rules" "$root/lib/udev/rules.d/"
	suppress_services_start "$root"
	propagate_host_resolv_conf "$root"
	make_utf8_locale "$root"
	apt_setup "$root"
	upgrade_chroot "$root"
	install_packages "$root" $BOOTSTRAP_PKGS $BOOTSTRAP_FUEL_PKGS
	recompress_initramfs "$root"
	copy_conf_files "$root"
	restore_resolv_conf "$root"
	cleanup_chroot "$root"
	mk_squashfs_image "$root"
}

root=`mktemp -d --tmpdir fuel-bootstrap-image.XXXXXXXXX`

main ()
{
	build_image "$root"
}

signal_chrooted_processes ()
{
	local root="$1"
	local signal="${2:-SIGTERM}"
	local max_attempts=10
	local timeout=2
	local count=0
	local found_processes
	[ ! -d "$root" ] && return 0
	while [ $count -lt $max_attempts ]; do
		found_processes=''
		for pid in `fuser $root 2>/dev/null`; do
			[ "$pid" = "kernel" ] && continue
			if [ "`readlink /proc/$pid/root`" = "$root" ]; then
				found_processes='yes'
				kill "-${signal}" $pid
			fi
		done
		[ -z "$found_processes" ] && break
		count=$((count+1))
		sleep $timeout
	done
}

final_cleanup ()
{
	signal_chrooted_processes "$root" SIGTERM
	signal_chrooted_processes "$root" SIGKILL
	for mnt in /tmp/local-apt /mnt/dst /mnt/src /mnt /proc; do
		if mountpoint -q "${root}${mnt}"; then
			umount "${root}${mnt}" || umount -l "${root}${mnt}" || true
		fi
	done
	if [ -z "$SAVE_TEMPS" ]; then
		rm -rf "$root"
	fi
}

trap final_cleanup 0
trap final_cleanup HUP TERM INT QUIT
main
