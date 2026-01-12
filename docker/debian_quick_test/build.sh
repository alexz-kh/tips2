#!/bin/bash


dist="dist-amd64"


if [[ ! -d docker-debian-artifacts ]]; then
  git clone -b ${dist} https://github.com/debuerreotype/docker-debian-artifacts.git
fi
