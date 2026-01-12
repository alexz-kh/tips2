#!/bin/bash

set -xe
set -o pipefail

ODIR="$(pwd)/temp"
mkdir -p ${ODIR}

M_PATH="/testing/openstack-pike/xenial/"
#xenial,xenial-security
M_DISTS="xenial"
M_SECTION='main'

#
M_NAME=$(echo ${M_PATH} | tr '/' '_')

stamp=$(date "+%Y_%m_%d_%H_%M_%S")
LOGDIR=${ODIR}/log/debmirror
DEBMLOG=${LOGDIR}/${stamp}.log
MIRRORDIR=${ODIR}/${M_NAME}
MIRROR_HOST=${MIRROR_HOST:-"mirror.mirantis.com"}
method=${CLONE_METHOD:-"rsync"}


function run_debmirror(){

mkdir -p ${LOGDIR}
mkdir -p ${MIRRORDIR}

if [[ ${method} == "rsync" ]] ; then
  m_root=":mirror/${M_PATH}"
#elif [[ ${method} == "http" ]] ; then
#  m_root="$MCP_VERSION/ubuntu"
else
  echo "LOG: Error: unsupported clone method!" 2>&1 | tee -a $DEBMLOG
  exit 1
fi

### Script body ###
echo "LOG: Start: $(date '+%Y_%m_%d_%H_%M_%S')"  2>&1 | tee -a $DEBMLOG

mkdir -p $(dirname ${DEBMLOG}) ${MIRRORDIR}
# Ubuntu General
echo "LOG: Ubuntu Mirror" 2>&1 | tee -a $DEBMLOG

debmirror --verbose --method=${method} --progress \
  --host=${MIRROR_HOST} \
  --arch=amd64 \
  --dist=${M_DISTS} \
  --root=${m_root} \
  --section=${M_SECTION} \
  --rsync-extra=none \
  --nosource \
  --no-check-gpg \
  $MIRRORDIR 2>&1 | tee -a $DEBMLOG

echo "LOG: Mirror size " 2>&1 | tee -a $DEBMLOG
du -hs "${MIRRORDIR}" 2>&1 | tee -a $DEBMLOG

echo "LOG: Finish:$(date '+%Y_%m_%d_%H_%M_%S')"  2>&1 | tee -a $DEBMLOG
}

run_debmirror
