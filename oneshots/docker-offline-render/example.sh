#!/bin/bash

# Docker run:
#
# docker run -v $(pwd)/../packer-templates/:/tests/ --hostname=apt01.mcp-offline.local --ulimit nofile=4096:8192 --cpus=4 -ti ubuntu:16.04 /bin/bash
#

export _BUILD_ID_VERSION=2018.8.0

export CLUSTER_NAME=mcp-offline
export CLUSTER_MODEL=https://github.com/Mirantis/mcp-offline-model.git
export MCP_VERSION=${_BUILD_ID_VERSION}
export DISTRIB_REVISION=${_BUILD_ID_VERSION}
#
export CLUSTER_MODEL_REF=${_BUILD_ID_VERSION}
export FORMULA_VERSION=${_BUILD_ID_VERSION}
export SALTSTACK_GPG="http://mirror.mirantis.com/${_BUILD_ID_VERSION}/saltstack-2017.7/xenial/SALTSTACK-GPG-KEY.pub"
export SALTSTACK_REPO="http://mirror.mirantis.com/${_BUILD_ID_VERSION}/saltstack-2017.7/xenial xenial main"
export APT_MIRANTIS_GPG="http://apt.mirantis.com/public.gpg"
export APT_MIRANTIS_SALT_REPO="http://apt.mirantis.com/xenial/ $FORMULA_VERSION salt"
export GIT_SALT_FORMULAS_SCRIPTS="https://github.com/salt-formulas/salt-formulas-scripts"
#
export TARGET=/json/reclass
#
apt-get update
apt-get install wget curl sudo git-core vim jq -y
cp -Lrv /tests/mirror-image/files/* /
# run bootstrap script
export PACKER_OFFLINE_BUILD=true # push to use local one script, from /tmp/
export BS_HOSTNAME="apt01"
bash -x /tests/mirror-image/scripts/salt_bootstrap.sh
# Scripts will install salt-master and all salt-formulas, using offline model.
#Script may fail during installation-those  issue can be ignored.
#After it will done, you can check rendered output via reclass and jq (still in docker) :
salt-key -L
# Accepted Keys:
# apt01.mcp-offline.local
# Show full render reclass for offline node:
apt-get install -y jq reclass
reclass -n apt01.mcp-offline.local -o json | jq '.parameters.aptly.server.mirror' >  ${TARGET}.aptly.server.json
reclass -n apt01.mcp-offline.local -o json | jq '.parameters.docker.client.registry' > ${TARGET}.docker.json
reclass -n apt01.mcp-offline.local -o json | jq '.parameters.git' > ${TARGET}.git.json
# Full render
reclass -n apt01.mcp-offline.local -o yaml | jq '.parameters' >  ${TARGET}.parameters.yaml
# Maas maas-ephemeral-v3 mirror
reclass -n apt01.mcp-offline.local -o json | jq '.parameters.maas.mirror' >  ${TARGET}.maas.mirror.json
# Debmirror
reclass -n apt01.mcp-offline.local -o json | jq '.parameters.debmirror.client.mirrors' >  ${TARGET}.debmirror.client.mirrrors.json
