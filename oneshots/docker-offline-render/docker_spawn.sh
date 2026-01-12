#!/bin/bash -e

#code_tag="2018.4.0"
code_tag="master"
#code_tag=testing

srv_volumes=" -v /home/alexz/work/imgs/share/trash/dockers/volumes:/srv/volumes/aptly"
nicev=" -v $(pwd)/_screenrc:/root/.screenrc:ro -v ${HOME}/.vimrc:/root/.vimrc:ro -v ${HOME}/.vim:/root/.vim:ro"
volumes="${nicev} -v $(pwd):/test1 -v $(pwd)/model:/srv/salt/reclass -v $(pwd)/salt-formulas-scripts:/srv/salt/scripts "
docker_image="ubuntu_16_quick_test:latest"
opts=" ${volumes} -u root:root --ulimit nofile=4096:8192 --cpus=2"

#offline_model="https://github.com/Mirantis/mcp-offline-model"
offline_model="ssh://azvyagintsev@gerrit.mcp.mirantis.net:29418/salt-models/infra"

# Flow
# _prepare
# docker_run
# run_in_docker

function _prepare(){
  if [[ ! -d model ]]; then
    git clone --recursive ${offline_model} model
    pushd model
      git checkout $code_tag
      git submodule update --init --recursive
    popd
  fi

  if [[ ! -d mcp-common-scripts ]]; then
    git clone https://github.com/Mirantis/mcp-common-scripts.git mcp-common-scripts
    pushd mcp-common-scripts
      git checkout ${code_tag}
    popd
  fi
  # used by scripts/salt_bootstrap.sh
  if [[ ! -d salt-formulas-scripts ]]; then
    git clone https://github.com/salt-formulas/salt-formulas-scripts salt-formulas-scripts
  #  pushd salt-formulas-scripts
  #    git checkout ${code_tag}
  #  popd
  fi
  if [[ ! -d packer-templates ]]; then
    git clone ssh://azvyagintsev@gerrit.mcp.mirantis.net:29418/mk/packer-templates packer-templates
  fi
}

function docker_run_cfg01(){
  #docker run --rm ${opts} -it docker-offline-render:2018.1 /bin/bash
  docker run --rm ${opts} --hostname=cfg01 -it ${docker_image} /bin/bash
}

function docker_run_apt01(){
  #docker run --rm ${opts} -it docker-offline-render:2018.1 /bin/bash
  docker run --rm ${srv_volumes} ${opts} --hostname=apt01 -it ${docker_image} /bin/bash
}

function docker_run_ci.mcp.mirantis.net(){
  #docker run --rm ${opts} -it docker-offline-render:2018.1 /bin/bash
  docker run --rm ${srv_volumes} ${opts} --hostname=ci.mcp.mirantis.net -it ${docker_image} /bin/bash
}

function _local_refresh(){
  salt-call saltutil.clear_cache
  salt-call saltutil.refresh_pillar
  salt-call saltutil.sync_all
}
### _prepare_ parts


function _prepare_ci.mcp.mirantis.net(){
  set -x
  cp -Lfrv packer-templates/mirror-image/files/* /
  rm -vf salt-formulas-scripts/.salt-master-setup.sh.passed
  rm -v /done_ubuntu_salt_bootstrap
  rm -rvf '/srv/salt/reclass/nodes/_generated/'
  #
  export CLUSTER_NAME="mcp_ci_prd"
  export FORMULA_VERSION=testing # from where install salt-formulas
  export PACKER_OFFLINE_BUILD=true
  # salt_bootstrap.sh related
  export BS_HOSTNAME=$(hostname -f)
  export CLUSTER_DOMAIN='mcp.mirantis.net'
  bash -x packer-templates/mirror-image/scripts/salt_bootstrap.sh || true
  _local_refresh
#

  echo "DONE _prepare_ci.mcp.mirantis.net"
}

function _prepare_apt01(){

  set -x
  cp -Lfrv packer-templates/mirror-image/files/* /
  rm -vf salt-formulas-scripts/.salt-master-setup.sh.passed
  #
  export CLUSTER_NAME="mcp-offline"
  export FORMULA_VERSION=testing # from where install salt-formulas
  export PACKER_OFFLINE_BUILD=true
  # https://raw.githubusercontent.com/Mirantis/mcp-common-scripts/master/mirror-image/salt-bootstrap.sh
  bash -x packer-templates/mirror-image/scripts/salt_bootstrap.sh || true
  _local_refresh
#
  salt-call -l debug state.apply linux.system.repo
  salt-call -l debug state.apply linux.system.apt
#
  apt-get install -y salt-formula-debmirror
  _local_refresh
#

  echo "DONE _prepare_apt01"
}

function run_in_docker(){

  echo "APT::Get::AllowUnauthenticated \"true\";" > /etc/apt/apt.conf.d/AllowUnauthenticated
  echo "deb [arch=amd64] http://apt.mirantis.com/xenial testing extra" > /etc/apt/sources.list.d/temp-mcp_salt.list
  echo "deb [arch=amd64] http://apt.mirantis.com/xenial testing salt"  >> /etc/apt/sources.list.d/temp-mcp_salt.list
  apt-get update
  apt-get install -y reclass gnupg jq
  rm -v /etc/apt/sources.list.d/temp-mcp_salt.list

  _hostname=$(hostname -f)

  case $_hostname in
       apt01)
            _prepare_apt01
            ;;
       ci.mcp.mirantis.net)
            _prepare_ci.mcp.mirantis.net
            ;;
       *)
            echo "wrong hostname?"
            ;;
  esac
#
}
# apt01.mcp-offline.local
# reclass -n apt01.mcp-offline.local -o json  | jq '.parameters.aptly.server.mirror | .[] | .source'
# reclass -n apt01.mcp-offline.local -o json  | jq '.parameters.docker.client.registry.image |.[] | .registry '



#docker pull ubuntu:16.04
#docker run -v $(pwd):/tests -u root:root --hostname=apt01 --ulimit nofile=4096:8192 --cpus=2 --rm -it  ubuntu:16.04 /bin/bash
## After it, you will be dropped into docker shell
## set env variables
#export CLUSTER_NAME=mcp-offline
#export CLUSTER_MODEL=https://github.com/Mirantis/mcp-offline-model.git
#export MCP_VERSION=testing
#export DISTRIB_REVISION=testing
##
#export CLUSTER_MODEL_REF=master
#export FORMULA_VERSION=testing
#export SALTSTACK_GPG="https://repo.saltstack.com/apt/ubuntu/16.04/amd64/2016.3/SALTSTACK-GPG-KEY.pub"
#export SALTSTACK_REPO="http://repo.saltstack.com/apt/ubuntu/16.04/amd64/2016.3 xenial main"
#export APT_MIRANTIS_GPG="http://apt.mirantis.com/public.gpg"
#export APT_MIRANTIS_SALT_REPO="http://apt.mirantis.com/xenial/ $FORMULA_VERSION salt"
#export GIT_SALT_FORMULAS_SCRIPTS="https://github.com/salt-formulas/salt-formulas-scripts"
#
##
#apt-get update && apt-get install wget curl sudo git-core vim jq -y
#cp -rv /tests/packer-templates/mirror-image/files/* /
## run bootstrap script
#export PACKER_OFFLINE_BUILD=true # push to use local one script, from /tmp/
#bash -x /tests/packer-templates/mirror-image/scripts/salt_bootstrap.sh
## Scripts will install salt-master and all salt-formulas, using offline model.
##Script may fail during installation-those  issue can be ignored. After it will done, you can check rendered output via reclass and jq (still in docker) :
#salt-key -L
## Accepted Keys:
## apt01.mcp-offline.local
## Show full render reclass for offline node:
#reclass -n apt01.mcp-offline.local



