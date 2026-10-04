#!/usr/bin/env python3
"""Bluetooth menu: on/off switch, known devices, click to connect/disconnect,
and a scan button to find and pair new devices. Uses bluetoothctl (BlueZ)."""
import os
import re
import shlex
import subprocess
import sys
from functools import partial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from popup import Popup, notify, relaunch_cmd, run_bg  # noqa: E402

CHECK = ""
MAC_LIKE = re.compile(r"^([0-9A-F]{2}[-:]){5}[0-9A-F]{2}$", re.I)


def btctl(*args: str) -> str:
    try:
        return subprocess.run(["bluetoothctl", *args], capture_output=True,
                              text=True, timeout=5).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def radio_unblocked() -> bool:
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


def powered() -> bool:
    return radio_unblocked() and "Powered: yes" in btctl("show")


def devices(kind: str | None = None) -> dict[str, str]:
    out = btctl("devices", kind) if kind else btctl("devices")
    found: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0] == "Device":
            found[parts[1]] = parts[2]
    return found


def bt_cmd(steps: list[list[str]], ok: str, fail: str) -> str:
    chain = " && ".join(shlex.join(["bluetoothctl", *s]) for s in steps)
    return f"{chain} && {notify('Bluetooth', ok)} || {notify('Bluetooth', fail)}"


class BtMenu(Popup):
    def __init__(self) -> None:
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
                          partial(self.pick, mac, name, is_on))
        if others:
            self.add_sep()
            self.add_label("New devices")
            for mac, name in list(others.items())[:10]:
                self.add_item(f"  {name}", partial(self.pair, mac, name))
        self.add_sep()
        self.add_item("Scan for devices", self.scan, dim=True)

    def toggle(self, state: bool) -> None:
        if state:
            run_bg(f"rfkill unblock bluetooth; sleep 1; bluetoothctl power on; sleep 1; {relaunch_cmd()}")
        else:
            run_bg("bluetoothctl power off; rfkill block bluetooth")
        self.destroy()

    def pick(self, mac: str, name: str, is_connected: bool) -> None:
        if is_connected:
            run_bg(bt_cmd([["disconnect", mac]], f"Disconnected {name}", f"Could not disconnect {name}"))
        else:
            run_bg(bt_cmd([["connect", mac]], f"Connected {name}", f"Could not connect {name}"))
        self.destroy()

    def pair(self, mac: str, name: str) -> None:
        run_bg(bt_cmd([["pair", mac], ["trust", mac], ["connect", mac]],
                      f"Paired and connected {name}", f"Could not pair {name}"))
        self.destroy()

    def scan(self) -> None:
        run_bg(f"{notify('Bluetooth', 'Scanning for 10 seconds…')}; "
               f"bluetoothctl --timeout 10 scan on >/dev/null; {relaunch_cmd()}")
        self.destroy()


if __name__ == "__main__":
    BtMenu().run()
