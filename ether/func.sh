#!/bin/bash

# https://bitcointalk.org/index.php?topic=1854250.msg18742952#msg18742952
# https://forum.bits.media/index.php?/topic/38879-nastroika-gtx-1060-pod-linux/
# https://forum.bits.media/index.php?/topic/38879-nastroika-gtx-1060-pod-linux/page-3
TOTAL_GPU="4"

function set_fan(){
  local speed=${1:-"auto"}
  local gpu=${2:-"all"}
  if [[ "${gpu}" == "all" ]];then
    for gpu in $(seq 0 ${TOTAL_GPU}); do
      if [[ ${speed} == "auto" ]]; then
        nvidia-settings -a "[gpu:${gpu}]/GPUFanControlState=0"
      else
        nvidia-settings -a "[gpu:${gpu}]/GPUFanControlState=1"
        nvidia-settings -a "[fan:${gpu}]/GPUTargetFanSpeed=${speed}"
      fi
    done
  else
    if [[ ${speed} == "auto" ]]; then
      nvidia-settings -a "[gpu:${gpu}]/GPUFanControlState=0"
    else
      nvidia-settings -a "[gpu:${gpu}]/GPUFanControlState=1"
      nvidia-settings -a "[fan:${gpu}]/GPUTargetFanSpeed=${speed}"
    fi
  fi
}

function check_pl() {
  local gpu=${1:-0}
  local value=${2:-140}
  if [[ $(nvidia-smi -i ${gpu} --format=csv,nounits,noheader --query-gpu=power.limit | awk -F "." '{print $1}') -eq ${value} ]] ; then
    echo "same"
  else 
    nvidia-smi -i ${gpu} -pm 1
    nvidia-smi -i ${gpu} -pl ${value}
  fi
}


function set_over(){
  local mclock=${1:-1500}
  local gpuclock=${2:-"-150"}
  local gpu=${3:-"all"}
  if [[ "${gpu}" == "all" ]];then
    for gpu in $(seq 0 ${TOTAL_GPU}); do
    check_pl ${gpu}
    nvidia-settings -a "[gpu:${gpu}]/GPUPowerMizerMode=1"
    nvidia-settings -a "[gpu:${gpu}]/GPUMemoryTransferRateOffset[3]=${mclock}"
    nvidia-settings -a "[gpu:${gpu}]/GPUGraphicsClockOffset[3]=${gpuclock}"
    done
  else
    check_pl ${gpu}
    nvidia-settings -a "[gpu:${gpu}]/GPUPowerMizerMode=1"
    nvidia-settings -a "[gpu:${gpu}]/GPUMemoryTransferRateOffset[3]=${mclock}"
    nvidia-settings -a "[gpu:${gpu}]/GPUGraphicsClockOffset[3]=${gpuclock}"
  fi
}

####Body
# set_fan 56 - set all fans to 56%
# set_fan 56 1 - set FAN1 to 56%
# set_fan auto - set all fans to auto
function do_init(){
export DISPLAY=:0
cpufreq-set -g performance -c 0
cpufreq-set -g performance -c 1
X :0 &
}
#nvidia-smi --format=csv,nounits --query-gpu=fan.speed 
#nvidia-settings -a "[fan:0]/GPUCurrentFanSpeed=70"
#while : ; do nvidia-smi dmon -d 1 -c 1 -s pucev ; date ;sleep 3 ; done

