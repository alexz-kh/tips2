FROM         ubuntu:latest
ENV container docker
#MAINTAINER 

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
        && echo 'APT::Get::Install-Recommends "false";'  >> /etc/apt/apt.conf.d/docker-clean \
        && echo 'APT::Get::Install-Suggests "false";'>> /etc/apt/apt.conf.d/docker-clean \
        \
        && echo 'Acquire::Languages "none";' > /etc/apt/apt.conf.d/docker-no-languages \
        \
        && echo 'Acquire::GzipIndexes "true"; Acquire::CompressionTypes::Order:: "gz";' > /etc/apt/apt.conf.d/docker-gzip-indexes

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -vf /lib/systemd/system/multi-user.target.wants/*; \
rm -vf /etc/systemd/system/*.wants/*; \
rm -vf /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*; \
rm -f /lib/systemd/system/anaconda.target.wants/*;

# delete all the apt list files since they're big and get stale quickly
RUN rm -rf /var/lib/apt/lists/*


COPY ./files/authorized_keys /root/.ssh/authorized_keys

# enable the universe
#RUN sed -i 's/^#\s*\(deb.*universe\)$/\1/g' /etc/apt/sources.list
RUN cd /etc/apt/; echo > sources.list; echo "deb http://cz.archive.ubuntu.com/ubuntu/ xenial main restricted universe multiverse\ndeb http://cz.archive.ubuntu.com/ubuntu/ xenial-updates main restricted universe multiverse\n" >> sources.list

RUN apt update && apt install -y iputils-ping wget curl openssh-server 

STOPSIGNAL SIGRTMIN+3
EXPOSE 22



# overwrite this with 'CMD []' in a dependent Dockerfile
CMD ["/sbin/init"]

#docker run -p 2200:22 --privileged --volume /sys/fs/cgroup:/sys/fs/cgroup --name=tmp --detach --entrypoint=/sbin/init s_test
# Doc:
# https://developers.redhat.com/blog/2016/09/13/running-systemd-in-a-non-privileged-container/
# https://developers.redhat.com/blog/2014/05/05/running-systemd-within-docker-container/
# https://github.com/moby/moby/issues/28614

