# Auto login root on tty1
sed -i 's|/sbin/getty|/sbin/getty --autologin root|g' /etc/init/tty1.conf

# Libvirt serial console support
cat << 'EOF' >> /etc/init/ttyS0.conf
# ttyS0 - getty
#
# This service maintains a getty on tty1 from the point the system is
# started until it is shut down again.

start on stopped rc RUNLEVEL=[2345] and (
            not-container or
            container CONTAINER=lxc or
            container CONTAINER=lxc-libvirt)

stop on runlevel [!2345]

respawn
exec /sbin/getty --autologin root -8 115200 ttyS0 xterm
EOF

# Disable password root login
usermod -p '!' root

# Disable SSH password authentication and permit root login
sed -i 's|[#]*PasswordAuthentication yes|PasswordAuthentication no|g' /etc/ssh/sshd_config
sed -i 's|[#]*PermitRootLogin no|PermitRootLogin yes|g' /etc/ssh/sshd_config
