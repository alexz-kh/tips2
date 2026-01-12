#!/bin/bash
mkdir -p lists
pushd lists/
curl http://apt.mirantis.com.s3.amazonaws.com/xenial/openstack/pike/dists/nightly/main/binary-amd64/Packages.gz | zcat > apt.os.pike.nightly
curl http://apt.mirantis.com.s3.amazonaws.com/xenial/openstack/pike/dists/proposed/main/binary-amd64/Packages.gz | zcat > apt.os.pike.proposed
curl http://apt.mirantis.com.s3.amazonaws.com/xenial/openstack/pike/dists/testing/main/binary-amd64/Packages.gz | zcat > apt.os.pike.testing
curl https://mirror.mirantis.com/proposed/openstack-pike/xenial/dists/xenial/main/binary-amd64/Packages.gz | zcat > mirror.os.pike.proposed
#
curl http://apt.mirantis.com.s3.amazonaws.com/xenial/openstack/pike/dists/2018.3.1/main/binary-amd64/Packages.gz | zcat > apt.os.pike.2018.3.1

#
curl http://apt.mirantis.com.s3.amazonaws.com/xenial/dists/nightly/salt/binary-amd64/Packages.gz | zcat > apt.salt.nightly
curl http://apt.mirantis.com.s3.amazonaws.com/xenial/dists/testing/salt/binary-amd64/Packages.gz | zcat > apt.salt.testing
curl http://apt.mirantis.com.s3.amazonaws.com/xenial/dists/proposed/salt/binary-amd64/Packages.gz | zcat > apt.salt.proposed
#
curl http://apt.mirantis.com.s3.amazonaws.com/xenial/dists/nightly/extra/binary-amd64/Packages.gz | zcat > apt.extra.nightly
curl http://apt.mirantis.com.s3.amazonaws.com/xenial/ceph/dists/2018.3.1/luminous/binary-amd64/Packages.gz | zcat > apt.ceph-luminous.2018.3.1

# upstream
curl https://mirror.mirantis.com/nightly/ubuntu/dists/xenial/main/binary-amd64/Packages.gz | zcat > upstream-ubuntu-xenial-main
curl https://mirror.mirantis.com/nightly/ubuntu/dists/xenial/multiverse/binary-amd64/Packages.gz | zcat > upstream-ubuntu-xenial-multiverse
curl https://mirror.mirantis.com/nightly/ubuntu/dists/xenial/restricted/binary-amd64/Packages.gz | zcat > upstream-ubuntu-xenial-restricted
curl https://mirror.mirantis.com/nightly/ubuntu/dists/xenial/universe/binary-amd64/Packages.gz | zcat > upstream-ubuntu-xenial-universe

popd

