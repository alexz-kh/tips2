%include fedora-live-base.ks
%include fedora-live-minimization.ks
%include fedora-xfce-common.ks

repo --name=epel --baseurl=https://dl.fedoraproject.org/pub/epel/6/x86_64/

lang en_US.UTF-8
keyboard us
timezone US/Eastern
auth --useshadow --passalgo=sha512
firewall --disabled
selinux --disabled
xconfig --startxonboot
zerombr
clearpart --all
part / --size 5120 --fstype ext4
services --enabled=NetworkManager,ModemManager,sshd
network --bootproto=dhcp --device=link --activate
rootpw r00tme
shutdown

%packages
acpid
rsync
htop
iftop
iotop
mc
tar
wget
curl
ntfs-3g
gparted
screen
ddrescue
lvm2
smartmontools
lm_sensors
sysbench
tcpdump
gnome-disk-utility
sleuthkit
hdparm
nfs-utils
nfs-utils-lib
libnfsidmap
lshw
strace
-abrt
-gnome-abrt
-emacs
-xscreensaver-extras
-xscreensaver-base
-xfce4-screenshooter
-xfce4-screenshooter
# Need for UI disks
#-sound-theme-freedesktop
-gnome-bluetooth
-gnome-bluetooth
-NetworkManager-bluetooth
-bluez-libs
-bluez-cups
-bluez
-desktop-backgrounds-compat
-f26-backgrounds-base
-pidgin
-gutenprint-cups
-leafpad
-cups
-@dial-up
-@multimedia
#-@xfce-apps
-@xfce-extra-plugins
-@xfce-media
-@xfce-office
%end

%post
# xfce configuration

# create /etc/sysconfig/desktop (needed for installation)
cat > /etc/sysconfig/desktop <<EOF
PREFERRED=/usr/bin/startxfce4
DISPLAYMANAGER=/usr/sbin/lightdm
EOF

cat >> /etc/rc.d/init.d/livesys << EOF

mkdir -p /home/liveuser/.config/xfce4

cat > /home/liveuser/.config/xfce4/helpers.rc << FOE
MailReader=sylpheed-claws
FileManager=Thunar
WebBrowser=firefox
FOE

# alexz
mkdir -p /home/liveuser/.ssh/
cat >> /home/liveuser/.ssh/authorized_keys << FOE
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGmNI+xV2sgIZX6tr5i4eQcxM4rkNoMiFbUuxtZYw5rKci9cSp9C/NC11VnJzpLG3lf11vLwTztlaM7hjdYlKoynpfDhfRhg1p5w/Pd/uoh6bO7KP/r2QuSpVsc6NGAHD2f0qxmrFX81xMG6zq0MCHXc+BGMZTKWAW7dMGsjJUnIa/wv24J25DOILoEBhclGQHx5r7R5ysqSOTdBEgN304KL8XPP+bAwDFTNJIwtfBdNt8jSv6yR2CyfB7t8pqXf93DvwaGBJfuu1r4gljj5ozCyvGExEtRTzvAC+oLq2NIfDOCC3iRWXrls3iDLZYxwm7VLcQSre4Yp6jfp+WuRI7 alexz
FOE

mkdir -p /root/.ssh/
echo -e "termcapinfo xterm* ti@:te@ \ndefscrollback 10000\n" >> /root/.screenrc
cat >> /root/.ssh/authorized_keys << FOE
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGmNI+xV2sgIZX6tr5i4eQcxM4rkNoMiFbUuxtZYw5rKci9cSp9C/NC11VnJzpLG3lf11vLwTztlaM7hjdYlKoynpfDhfRhg1p5w/Pd/uoh6bO7KP/r2QuSpVsc6NGAHD2f0qxmrFX81xMG6zq0MCHXc+BGMZTKWAW7dMGsjJUnIa/wv24J25DOILoEBhclGQHx5r7R5ysqSOTdBEgN304KL8XPP+bAwDFTNJIwtfBdNt8jSv6yR2CyfB7t8pqXf93DvwaGBJfuu1r4gljj5ozCyvGExEtRTzvAC+oLq2NIfDOCC3iRWXrls3iDLZYxwm7VLcQSre4Yp6jfp+WuRI7 alexz
FOE

# disable screensaver locking (#674410)
cat >> /home/liveuser/.xscreensaver << FOE
mode:           off
lock:           False
dpmsEnabled:    False
FOE

# deactivate xfconf-migration (#683161)
rm -f /etc/xdg/autostart/xfconf-migration-4.6.desktop || :

# deactivate xfce4-panel first-run dialog (#693569)
mkdir -p /home/liveuser/.config/xfce4/xfconf/xfce-perchannel-xml
cp /etc/xdg/xfce4/panel/default.xml /home/liveuser/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml

# set up lightdm autologin
sed -i 's/^#autologin-user=.*/autologin-user=liveuser/' /etc/lightdm/lightdm.conf
sed -i 's/^#autologin-user-timeout=.*/autologin-user-timeout=0/' /etc/lightdm/lightdm.conf
#sed -i 's/^#show-language-selector=.*/show-language-selector=true/' /etc/lightdm/lightdm-gtk-greeter.conf

# set Xfce as default session, otherwise login will fail
sed -i 's/^#user-session=.*/user-session=xfce/' /etc/lightdm/lightdm.conf

# Show harddisk install on the desktop
sed -i -e 's/NoDisplay=true/NoDisplay=false/' /usr/share/applications/liveinst.desktop
mkdir /home/liveuser/Desktop
cp /usr/share/applications/liveinst.desktop /home/liveuser/Desktop

# and mark it as executable (new Xfce security feature)
chmod +x /home/liveuser/Desktop/liveinst.desktop

# this goes at the end after all other changes. 
chown -R liveuser:liveuser /home/liveuser
restorecon -R /home/liveuser

# alexz
systemctl enable sshd
systemctl start sshd
systemctl stop smartd
#

cat >> /etc/yum.repos.d/epel.repo <<EOF
[epel]
baseurl=https://dl.fedoraproject.org/pub/epel/7/x86_64/
enabled=1
gpgcheck=0
EOF

cat >> /etc/yum.repos.d/rpmfusion.repo <<EOF
[rpmfusion-free]
name=RPM Fusion for Fedora $releasever - Free
#baseurl=http://download1.rpmfusion.org/free/fedora/releases/$releasever/Everything/$basearch/os/
metalink=https://mirrors.rpmfusion.org/metalink?repo=free-fedora-$releasever&arch=$basearch
enabled=1
metadata_expire=14d
type=rpm-md
gpgcheck=0
repo_gpgcheck=0
#gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rpmfusion-free-fedora-$releasever
[rpmfusion-free-updates]
name=RPM Fusion for Fedora $releasever - Free - Updates
#baseurl=http://download1.rpmfusion.org/free/fedora/updates/$releasever/$basearch/
metalink=https://mirrors.rpmfusion.org/metalink?repo=free-fedora-updates-released-$releasever&arch=$basearch
enabled=1
type=rpm-md
gpgcheck=0
repo_gpgcheck=0
#gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rpmfusion-free-fedora-$releasever
EOF

dnf clean all

EOF

%end

