#!/bin/bash

while

TIME="$(date +"%m/%d %I:%M")"

BATTERY=$(cat /sys/class/power_supply/BAT0/capacity)

WATTAGE=$(awk '{printf "%.1f", $1 / 1000000}' /sys/class/power_supply/BAT0/power_now)

CPUTEMP=$(cat /sys/devices/platform/coretemp.*/hwmon/hwmon*/temp*_input 2>/dev/null \
 | sort -nr | head -n1 | awk '{printf "%d", $1/1000}')

CPUFRQ=$(cat /sys/bus/cpu/devices/cpu*/cpufreq/scaling_cur_freq 2>/dev/null \
 | sort -nr | head -n1 | awk '{printf "%.1f", $1/1000000}')

GPUFRQ=$(awk '{printf "%.1f", $1 / 100}' /sys/class/drm/card0/gt_cur_freq_mhz)


printf `"[""td":`%s`"] "       " [""gpufreq":`%s`"][""cputemp":`%s`"][""cpufrq":`%s`"][""bat":`%s`"][""wat":%s"]"` \
"[""$TIME""] ""           "" [GPU:""$GPUFRQ"GHZ]"[CPU:""$CPUFRQ"GHZ"@""$CPUTEMP"*c"][""$BATTERY"%"|""$WATTAGE"W"]" 2>/dev/null


do sleep 2;
done
