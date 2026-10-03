#!/bin/sh
mako &
(
  while true; do
    cap=$(cat /sys/class/power_supply/BAT0/capacity)
    status=$(cat /sys/class/power_supply/BAT0/status)
    if [ "$status" = "Discharging" ] && [ "$cap" -le 20 ]; then
      notify-send -a battery -u critical "Low battery" "${cap}% remaining"
    fi
    sleep 120
  done
) &
