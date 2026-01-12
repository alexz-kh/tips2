#!/bin/bash -xe
# Motd
apt-get -y install update-motd
rm -vf /etc/update-motd.d/*
echo "BUILD_TIMESTAMP=$(date '+%Y-%m-%d-%H-%M-%S' -u)" > /etc/image_version
echo "BUILD_TIMESTAMP_RFC=\"$(date -u -R)\"" >> /etc/image_version
cat << 'EOF' >> /etc/update-motd.d/00-header
#!/bin/sh
#
#    00-header - create the header of the MOTD
#
[ -r /etc/image_version ] && . /etc/image_version
echo "Ubuntu 20 \"Focal\" cloud image"
echo "Build date: ${BUILD_TIMESTAMP_RFC}"
EOF
chmod +x /etc/update-motd.d/00-header

