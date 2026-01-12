#!/bin/bash -xe

# Libvirt serial console support
cat << EOF >> /etc/systemd/system/serial-getty@.service
[Unit]
Description=Getty on %I
Documentation=man:agetty(8) man:systemd-getty-generator(8)
Documentation=http://0pointer.de/blog/projects/serial-console.html
After=systemd-user-sessions.service plymouth-quit-wait.service
After=rc-local.service

Before=getty.target
IgnoreOnIsolate=yes

ConditionPathExists=/dev/ttyS0

[Service]
ExecStart=-/sbin/agetty -8 --noclear %I 115200 \$TERM
Type=idle
Restart=always
RestartSec=0
UtmpIdentifier=%I
TTYPath=/dev/%I
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes
KillMode=process
IgnoreSIGPIPE=no
SendSIGHUP=yes

Environment=LANG= LANGUAGE= LC_CTYPE= LC_NUMERIC= LC_TIME= LC_COLLATE= LC_MONETARY= LC_MESSAGES= LC_PAPER= LC_NAME= LC_ADDRESS= LC_TELEPHONE= LC_MEASUREMENT= LC_IDENTIFICATION=

[Install]
WantedBy=getty.target
DefaultInstance=ttyS0
EOF

systemctl daemon-reload
systemctl enable serial-getty@ttyS0.service

# Disable password root login
usermod -p '!' root

# Drop default 'ubuntu' user
userdel -rf ubuntu || true

# Disable SSH password authentication and permit root login
sed -i 's|[#]*PasswordAuthentication yes|PasswordAuthentication no|g' /etc/ssh/sshd_config
sed -i 's|[#]*PermitRootLogin.*|PermitRootLogin no|g' /etc/ssh/sshd_config
rm -v /etc/ssh/sshd_config.d/packet.conf || true
