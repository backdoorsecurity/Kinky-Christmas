#!/bin/bash
# One-shot stats for waybar custom/sysstats (GPU/CPU; bat % is the battery module).

CPUTEMP=$(cat /sys/devices/platform/coretemp.*/hwmon/hwmon*/temp*_input 2>/dev/null \
  | sort -nr | head -n1 | awk '{printf "%d", $1/1000}')

CPUFRQ=$(cat /sys/bus/cpu/devices/cpu*/cpufreq/scaling_cur_freq 2>/dev/null \
  | sort -nr | head -n1 | awk '{printf "%.1f", $1/1000000}')

GPU_PATH=$(ls /sys/class/drm/card*/gt_cur_freq_mhz 2>/dev/null | head -n1)
GPUFRQ=
if [ -n "$GPU_PATH" ]; then
  GPUFRQ=$(awk '{printf "%.1f", $1 / 100}' "$GPU_PATH")
fi

printf '[GPU:%sGHZ][CPU:%sGHZ@%s*c]' \
  "${GPUFRQ:-?}" "${CPUFRQ:-?}" "${CPUTEMP:-?}"
