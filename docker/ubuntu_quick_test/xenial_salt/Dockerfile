FROM mirantis/salt:saltstack-ubuntu-xenial-salt-2017.7

ENV DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true \
    LANG=C.UTF-8 \
    LANGUAGE=$LANG \
    TERM=xterm
SHELL ["/bin/bash", "-xec"]
# a few minor docker-specific tweaks
# see https://github.com/docker/docker/blob/master/contrib/mkimage/debootstrap
RUN set -xe \
	\
	&& echo '#!/bin/sh' > /usr/sbin/policy-rc.d \
	&& echo 'exit 101' >> /usr/sbin/policy-rc.d \
	&& chmod +x /usr/sbin/policy-rc.d \
	\
	&& dpkg-divert --local --rename --add /sbin/initctl \
	&& cp -a /usr/sbin/policy-rc.d /sbin/initctl \
	&& sed -i 's/^exit.*/exit 0/' /sbin/initctl \
	\
	&& echo 'force-unsafe-io' > /etc/dpkg/dpkg.cfg.d/docker-apt-speedup \
	\
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
	&& echo 'APT::Get::Install-Recommends "false"; APT::Get::Install-Suggests "false";' > /etc/apt/apt.conf.d/docker-recommends

# make systemd-detect-virt return "docker"
# See: https://github.com/systemd/systemd/blob/aa0c34279ee40bce2f9681b496922dedbadfca19/src/basic/virt.c#L434
RUN mkdir -p /run/systemd && echo 'docker' > /run/systemd/container


RUN cd /etc/apt/ && echo > sources.list \
  && echo "deb [arch=amd64] http://ua.archive.ubuntu.com/ubuntu xenial main restricted universe multiverse" >> sources.list \
  && echo "deb [arch=amd64] http://ua.archive.ubuntu.com/ubuntu xenial-updates main restricted universe multiverse" >> sources.list \
  && echo "deb [arch=amd64] http://ua.archive.ubuntu.com/ubuntu xenial-backports main restricted universe multiverse" >> sources.list \
  && echo "deb [arch=amd64] http://mirror.mirantis.com/nightly/extra/xenial xenial main" >> sources.list.d/mcp_extra.list \
  && echo "deb [arch=amd64] http://apt.mirantis.com/xenial nightly salt" > sources.list.d/mcp_salt.list \
  && echo 'Acquire::Languages "none";' >> apt.conf.d/99alexz \
  && echo 'Acquire::GzipIndexes "true"; Acquire::CompressionTypes::Order:: "gz";' >> apt.conf.d/99alexz \
  && echo 'APT::Get::Install-Recommends "false"; APT::Get::Install-Suggests "false";' >> apt.conf.d/99alexz \
  && echo 'APT::Get::AllowUnauthenticated "true";' >> apt.conf.d/99alexz \
  && apt-get update && apt-get  upgrade -y \
  && apt-get install -y vim git-core screen wget curl apt-transport-https sudo iputils-ping dnsutils lz4cat \
  && apt-get install -y python-pip python3-pip python-virtualenv python3-virtualenv python-yaml autoconf build-essential \
  && apt-get install -y reclass salt-formula* \
  && mkdir -p /etc/reclass/

#RUN pip install -U pip #  python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install --upgrade pip setuptools wheel \
    &&  pip install git+https://github.com/dis-xcom/reclass-tools
COPY files/etc/reclass/reclass-config.yml /etc/reclass/reclass-config.yml

# Cleanup.
#RUN apt-get -y purge libx11-data xauth libxmuu1 libxcb1 libx11-6 libxext6 \
#    ppp pppconfig pppoeconf popularity-contest cpp gcc g++ libssl-doc
RUN apt-get -y autoremove; apt-get -y clean;
RUN rm -rf /root/.cache
RUN rm -rf /var/lib/apt/lists/*

# overwrite this with 'CMD []' in a dependent Dockerfile
CMD ["/bin/bash"]

# Build:
# docker build --no-cache -t ubuntu_16_quick_test_salt17:latest .
# docker tag ubuntu_16_quick_test_salt17:latest alexz0kh/ubuntu_16_quick_test_salt17:latest
# docker push alexz0kh/ubuntu_16_quick_test_salt17:latest
