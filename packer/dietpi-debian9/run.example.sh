#!/bin/bash

export PACKER_LOG=1
export PACKER_KEY_INTERVAL=10ms
# For qemu test-build:
rm -rf images/
packer build -only=qemu -parallel=false -on-error=ask debian9.json
# rm -rf ~/.packer.d/
