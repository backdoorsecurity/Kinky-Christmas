#!/bin/bash
# Keep Intel turbo and energy bias matched to AC vs battery.

set -u

write_glob() {
    local pattern=$1
    local value=$2
    local path old_nullglob
    old_nullglob=$(shopt -p nullglob)
    shopt -s nullglob
    # shellcheck disable=SC2086
    for path in $pattern; do
        if [[ -w $path ]]; then
            printf '%s\n' "$value" >"$path" || true
        fi
    done
    eval "$old_nullglob"
}

on_ac() {
    local dir type saw_mains=0 saw_battery=0
    for dir in /sys/class/power_supply/*; do
        [[ -r $dir/type ]] || continue
        type=$(<"$dir/type")
        case $type in
            Mains|USB)
                saw_mains=1
                if [[ -r $dir/online && $(<"$dir/online") == 1 ]]; then
                    return 0
                fi
                ;;
            Battery)
                saw_battery=1
                ;;
        esac
    done
    if [[ $saw_mains -eq 1 ]]; then
        return 1
    fi
    [[ $saw_battery -eq 0 ]]
}

apply_profile() {
    local turbo_off=$1
    local boost=$2
    local governor=$3
    local bias=$4
    local preference=$5
    write_glob /sys/devices/system/cpu/intel_pstate/no_turbo "$turbo_off"
    write_glob /sys/devices/system/cpu/cpufreq/boost "$boost"
    write_glob '/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor' "$governor"
    write_glob '/sys/devices/system/cpu/cpu*/power/energy_perf_bias' "$bias"
    write_glob '/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference' "$preference"
}

apply_ac() {
    apply_profile 0 1 performance 0 performance
}

apply_battery() {
    apply_profile 1 0 powersave 15 power
}

last=""
refresh() {
    local mode
    if on_ac; then
        mode=ac
    else
        mode=battery
    fi
    [[ $mode == "$last" ]] && return 0
    last=$mode
    "apply_${mode}"
}

refresh
if command -v udevadm >/dev/null; then
    set -o pipefail
    udevadm monitor --udev --subsystem-match=power_supply | while read -r _; do
        refresh
    done
else
    while true; do
        sleep 15
        refresh
    done
fi
