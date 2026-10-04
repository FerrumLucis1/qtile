#!/usr/bin/env python3
"""Battery menu: charge, status and time left, plus brightness sliders for the
laptop screen (brightnessctl) and any external monitors (ddcutil, if installed)."""
import glob
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from popup import Popup  # noqa: E402

BAT = "/sys/class/power_supply/BAT0/"


def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def num(path):
    try:
        return int(read(path))
    except ValueError:
        return 0


def time_left(status):
    """'2h 10m left' / '45m to full' from charge or energy counters, or ''."""
    for now, full, rate in (("charge_now", "charge_full", "current_now"),
                            ("energy_now", "energy_full", "power_now")):
        n, f, r = num(BAT + now), num(BAT + full), num(BAT + rate)
        if n and r:
            if status == "Discharging":
                hours, label = n / r, "left"
            elif status == "Charging":
                hours, label = (f - n) / r, "to full"
            else:
                return ""
            return f"{int(hours)}h {int(hours * 60 % 60)}m {label}"
    return ""


def laptop_brightness():
    try:
        out = subprocess.run(["brightnessctl", "-m"], capture_output=True, text=True, timeout=2).stdout
        return int(out.strip().split(",")[3].rstrip("%"))
    except Exception:
        return None


def external_connected():
    return any(read(p) == "connected" for p in glob.glob("/sys/class/drm/card*-*/status")
               if "eDP" not in p and "LVDS" not in p)


def ddc_displays():
    """[(display_number, name, brightness)] for monitors that answer DDC/CI."""
    try:
        out = subprocess.run(["ddcutil", "detect", "--brief"], capture_output=True, text=True, timeout=8).stdout
    except Exception:
        return []
    found, num_, name = [], None, None
    for line in out.splitlines() + ["Display end"]:
        line = line.strip()
        if line.startswith("Display "):
            if num_:
                found.append((num_, name or f"Monitor {num_}"))
            num_ = line.split()[1] if line.split()[1].isdigit() else None
            name = None
        elif line.startswith("Monitor:") and num_:
            parts = line.split(":", 1)[1].split(":")
            name = parts[1].strip() if len(parts) > 1 and parts[1].strip() else parts[0].strip()
    result = []
    for n, nm in found:
        try:
            v = subprocess.run(["ddcutil", "--display", n, "getvcp", "10", "--brief"],
                               capture_output=True, text=True, timeout=5).stdout.split()
            cur, mx = int(v[3]), int(v[4]) or 100
            result.append((n, nm, round(cur * 100 / mx)))
        except Exception:
            pass
    return result


class BatMenu(Popup):
    def __init__(self):
        super().__init__("batmenu", 280)
        pct, status = num(BAT + "capacity"), read(BAT + "status") or "Unknown"
        self.add_label(f"Battery {pct}%  ·  {status}", dim=False)
        left = time_left(status)
        if left:
            self.add_label(left)
        self.add_sep()

        level = laptop_brightness()
        if level is not None:
            self.add_label("Laptop screen", dim=False)
            self.add_slider(max(level, 1), self.set_laptop, lo=1)

        if external_connected():
            if not shutil.which("ddcutil"):
                self.add_label("Install ddcutil for monitor brightness")
            else:
                displays = ddc_displays()
                if not displays:
                    self.add_label("Monitor doesn't support brightness control")
                for n, name, val in displays:
                    self.add_label(name, dim=False)
                    self.add_slider(val, lambda v, d=n: self.set_ddc(d, v), delay=400)

    def set_laptop(self, v):
        subprocess.Popen(["brightnessctl", "-q", "set", f"{v}%"])

    def set_ddc(self, display, v):
        subprocess.Popen(["ddcutil", "--display", display, "setvcp", "10", str(v)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    BatMenu().run()
