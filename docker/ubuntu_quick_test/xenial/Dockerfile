FROM ubuntu:16.04
#FROM busybox:latest
# https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-root.tar.gz
#ADD xenial-server-cloudimg-amd64-root.tar.gz ./

ENV DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true \
    LANG=C.UTF-8 \
    LANGUAGE=$LANG \
    TERM=xterm
# Use `;` instead `&&` where posible! somehow, pipefail may be ignored!
SHELL ["/bin/bash", "-o", "pipefail", "-xec"]
# a few minor docker-specific tweaks
# see https://github.com/docker/docker/blob/master/contrib/mkimage/debootstrap
RUN set -xe \
	\
	&& echo '#!/bin/sh' > /usr/sbin/policy-rc.d \
	&& echo 'exit 101' >> /usr/sbin/policy-rc.d \
	&& chmod +x /usr/sbin/policy-rc.d \
	&& dpkg-divert --local --rename --add /sbin/initctl \
	&& cp -a /usr/sbin/policy-rc.d /sbin/initctl \
	&& sed -i 's/^exit.*/exit 0/' /sbin/initctl \
	&& echo 'force-unsafe-io' > /etc/dpkg/dpkg.cfg.d/docker-apt-speedup \
	&& echo 'DPkg::Post-Invoke { "rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };' > /etc/apt/apt.conf.d/docker-clean \
	&& echo 'APT::Update::Post-Invoke { "rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true"; };' >> /etc/apt/apt.conf.d/docker-clean \
	&& echo 'Dir::Cache::pkgcache ""; Dir::Cache::srcpkgcache "";' >> /etc/apt/apt.conf.d/docker-clean \
# https://github.com/docker/docker/blob/9a9fc01af8fb5d98b8eec0740716226fadb3735c/contrib/mkimage/debootstrap#L134-L151
	&& echo 'Apt::AutoRemove::SuggestsImportant "false";' > /etc/apt/apt.conf.d/docker-autoremove-suggests \
	\
	&& echo 'Acquire::Languages "none";' > /etc/apt/apt.conf.d/docker-no-languages \
	\
	&& echo 'Acquire::GzipIndexes "true"; Acquire::CompressionTypes::Order:: "gz";' > /etc/apt/apt.conf.d/docker-gzip-indexes \
	\
	&& echo 'APT::Get::Install-Recommends "false"; APT::Get::Install-Suggests "false";' > /etc/apt/apt.conf.d/docker-recommends \
	&& mkdir -p /run/systemd && echo 'docker' > /run/systemd/container \
#
  && cd /etc/apt/ && echo > sources.list \
  && echo "deb [arch=amd64] http://ua.archive.ubuntu.com/ubuntu xenial main restricted universe multiverse" >> sources.list \
  && echo "deb [arch=amd64] http://ua.archive.ubuntu.com/ubuntu xenial-updates main restricted universe multiverse" >> sources.list \
  && echo "deb [arch=amd64] http://ua.archive.ubuntu.com/ubuntu xenial-security main restricted universe multiverse" >> sources.list \
  && echo "deb [arch=amd64] http://ua.archive.ubuntu.com/ubuntu xenial-backports main restricted universe multiverse" >> sources.list \
  && echo 'Acquire::Languages "none";' > apt.conf.d/docker-no-languages \
  && echo 'Acquire::GzipIndexes "true"; Acquire::CompressionTypes::Order:: "gz";' > apt.conf.d/docker-gzip-indexes \
  && echo 'APT::Get::Install-Recommends "false"; APT::Get::Install-Suggests "false";' > apt.conf.d/docker-recommends \
  && apt-get update && apt-get  upgrade -y \
#
  && apt-get install -y vim git-core screen wget curl apt-transport-https sudo iputils-ping dnsutils liblz4-tool libssl-dev net-tools openssh-client \
  && apt-get install -y python-pip python3-pip python-virtualenv python3-virtualenv python3-venv python-yaml autoconf build-essential \
  && apt-get install -y docker.io \
#  && pip install -U pip \
# Cleanup
#  && apt-get remove -y --purge openssh-client manpages-dev manpages \
  &&  apt-get -y autoremove; apt-get -y clean \
  && rm -rf /root/.cache \
  && rm -rf /var/lib/apt/lists/* \

# overwrite this with 'CMD []' in a dependent Dockerfile
CMD ["/bin/bash"]

# Build:
# docker build --squash --no-cache -t ubuntu_16_quick_test:latest .
# docker tag ubuntu_16_quick_test:latest alexz0kh/ubuntu_16_quick_test:latest
# docker push alexz0kh/ubuntu_16_quick_test:latest
