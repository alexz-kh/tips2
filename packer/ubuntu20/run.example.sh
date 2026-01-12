#!/bin/bash

# Docs:
# - https://wiki.ubuntu.com/FoundationsTeam/AutomatedServerInstalls
# - https://wiki.ubuntu.com/FoundationsTeam/AutomatedServerInstalls/ConfigReference
# - https://cloudinit.readthedocs.io/en/latest/topics/datasources/nocloud.html
# - https://discourse.ubuntu.com/t/please-test-autoinstalls-for-20-04/15250/53
#   https://gist.github.com/s3rj1k/55b10cd20f31542046018fcce32f103e
#   https://github.com/Instituto-i2ds/packer-template-ubuntu20.04/blob/main/ubuntu2004.json
#   https://gist.github.com/anedward01/b68e00bb2dcfa4f1335cd4590cbc8484#file-user-data-L36
#   https://curtin.readthedocs.io/en/latest/topics/storage.html

# TODO:
# optimize install-from-iso phase to
# make it quick, using correct ubuntu repo mirror
# disable kernel\etc update
# disable external network usage

# Packer: 1.7.8

# Those script - only example for variables, which should be passed to packer and
# overwrite variables under /scripts/ directory

export IMAGE_NAME="ubuntu-20-04-x64"

###
# Hard-coded folder in template
export PACKER_IMAGES_CACHE="${HOME}/packer_images_cache/"
mkdir -p "${PACKER_IMAGES_CACHE}"

export PACKER_KEY_INTERVAL='10ms'
export PACKER_LOG=1
# For qemu test-build:
packer build -only=qemu -on-error=ask template.json
#rm -rf ~/.packer.d/

