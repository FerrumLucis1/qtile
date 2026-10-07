#!/bin/sh
mako &

# low-battery warning - laptop only (the desktop has no battery)
bat=$(ls -d /sys/class/power_supply/BAT* 2>/dev/null | head -n1)
if [ -n "$bat" ]; then
  (
    while true; do
      cap=$(cat "$bat/capacity")
      status=$(cat "$bat/status")
      if [ "$status" = "Discharging" ] && [ "$cap" -le 20 ]; then
        notify-send -a battery -u critical "Low battery" "${cap}% remaining"
      fi
      sleep 120
    done
  ) &
fi
