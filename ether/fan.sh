#!/bin/bash
 
export DISPLAY=:0
 
NUM_CARDS=5
NS="/usr/bin/nvidia-settings"
source func.sh
 
while true
do
for ((i=0; i<$NUM_CARDS;i++))
{
  GPU_TEMP=`nvidia-smi -i $i --query-gpu=temperature.gpu --format=csv,noheader`
  sleep 1
  FAN_SPEED=`nvidia-smi -i $i --query-gpu=fan.speed --format=csv,noheader,nounits`
  sleep 1
  if (( $GPU_TEMP<=51 )) ; then
    to_s=48
  elif (( 52<=$GPU_TEMP && $GPU_TEMP<=60 )) ; then
    to_s=50
  elif (( 61<=$GPU_TEMP && $GPU_TEMP<=69 )) ; then
    to_s=56
  elif (( 70<=$GPU_TEMP && $GPU_TEMP<=72 )) ; then
    to_s=58
  elif (( 73<=$GPU_TEMP && $GPU_TEMP<=78 )) ; then
    to_s=65
  else 
    echo "VGA:${i} ${GPU_TEMP}C; FAN:${FAN_SPEED} => auto"
    set_fan "auto" ${i}  2&>1 > /dev/null
    return
  fi
  if (( $FAN_SPEED != $to_s )); then
    date
    echo "VGA:${i} ${GPU_TEMP}C; FAN:${FAN_SPEED} => ${to_s}"
    set_fan ${to_s} ${i} 2&>1 > /dev/null
  fi
}
sleep 10
done

