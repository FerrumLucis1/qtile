#!/usr/bin/env python3
"""Bluetooth menu: on/off switch, known devices, click to connect/disconnect,
and a scan button to find and pair new devices. Uses bluetoothctl (BlueZ)."""
import os
import re
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from popup import Popup, notify, relaunch_cmd, run_bg  # noqa: E402

CHECK = ""
MAC_LIKE = re.compile(r"^([0-9A-F]{2}[-:]){5}[0-9A-F]{2}$", re.I)


def btctl(*args):
    try:
        return subprocess.run(["bluetoothctl", *args], capture_output=True,
                              text=True, timeout=5).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def radio_unblocked():
    import glob
    for t in glob.glob("/sys/class/rfkill/*/type"):
        try:
            if open(t).read().strip() == "bluetooth":
                d = t[:-4]
                if open(d + "soft").read().strip() == "1" or open(d + "hard").read().strip() == "1":
                    return False
        except OSError:
            pass
    return True


def powered():
    return radio_unblocked() and "Powered: yes" in btctl("show")


def devices(kind=None):
    out = btctl("devices", kind) if kind else btctl("devices")
    found = {}
    for line in out.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0] == "Device":
            found[parts[1]] = parts[2]
    return found


def bt_cmd(steps, ok, fail):
    chain = " && ".join(shlex.join(["bluetoothctl", *s]) for s in steps)
    return f"{chain} && {notify('Bluetooth', ok)} || {notify('Bluetooth', fail)}"


class BtMenu(Popup):
    def __init__(self):
        super().__init__("btmenu", 260)
        on = powered()
        self.add_switch("Bluetooth", on, self.toggle)
        if not on:
            return
        self.add_sep()
        paired = devices("Paired")
        connected = devices("Connected")
        others = {m: n for m, n in devices().items()
                  if m not in paired and not MAC_LIKE.match(n)}
        if not paired:
            self.add_label("No paired devices")
        for mac, name in sorted(paired.items(), key=lambda kv: (kv[0] not in connected, kv[1])):
            is_on = mac in connected
            self.add_item(f"{CHECK if is_on else ' '} {name}",
                          lambda m=mac, n=name, c=is_on: self.pick(m, n, c))
        if others:
            self.add_sep()
            self.add_label("New devices")
            for mac, name in list(others.items())[:10]:
                self.add_item(f"  {name}", lambda m=mac, n=name: self.pair(m, n))
        self.add_sep()
        self.add_item("Scan for devices", self.scan, dim=True)

    def toggle(self, state):
        if state:
            run_bg(f"rfkill unblock bluetooth; sleep 1; bluetoothctl power on; sleep 1; {relaunch_cmd()}")
        else:
            run_bg("bluetoothctl power off; rfkill block bluetooth")
        self.destroy()

    def pick(self, mac, name, is_connected):
        if is_connected:
            run_bg(bt_cmd([["disconnect", mac]], f"Disconnected {name}", f"Could not disconnect {name}"))
        else:
            run_bg(bt_cmd([["connect", mac]], f"Connected {name}", f"Could not connect {name}"))
        self.destroy()

    def pair(self, mac, name):
        run_bg(bt_cmd([["pair", mac], ["trust", mac], ["connect", mac]],
                      f"Paired and connected {name}", f"Could not pair {name}"))
        self.destroy()

    def scan(self):
        run_bg(f"{notify('Bluetooth', 'Scanning for 10 seconds…')}; "
               f"bluetoothctl --timeout 10 scan on >/dev/null; {relaunch_cmd()}")
        self.destroy()


if __name__ == "__main__":
    BtMenu().run()
