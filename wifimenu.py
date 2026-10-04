#!/usr/bin/env python3
"""Wi-Fi menu: on/off switch, nearby networks, click to connect/disconnect.
Uses NetworkManager (nmcli). Run with --password SSID to show the password box."""
import os
import re
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from popup import Popup, notify, relaunch_cmd, run_bg  # noqa: E402

CHECK, LOCK = "", ""


def nm(*args):
    return subprocess.run(["nmcli", *args], capture_output=True, text=True).stdout


def fields(line):
    return [f.replace("\\:", ":") for f in re.split(r"(?<!\\):", line)]


def wifi_enabled():
    return nm("radio", "wifi").strip() == "enabled"


def saved_networks():
    names = set()
    for line in nm("-t", "-f", "NAME,TYPE", "connection", "show").splitlines():
        f = fields(line)
        if len(f) >= 2 and f[1] == "802-11-wireless":
            names.add(f[0])
    return names


def networks():
    seen = {}
    for line in nm("-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "dev", "wifi", "list").splitlines():
        f = (fields(line) + ["", "", "", ""])[:4]
        inuse, ssid, sig, sec = f[0] == "*", f[1], int(f[2] or 0), f[3]
        if not ssid:
            continue
        prev = seen.get(ssid, (False, 0, sec))
        seen[ssid] = (prev[0] or inuse, max(prev[1], sig), sec)
    return sorted(seen.items(), key=lambda kv: (not kv[1][0], -kv[1][1]))[:12]


def connect_cmd(ssid, password=None):
    cmd = ["nmcli", "dev", "wifi", "connect", ssid]
    if password:
        cmd += ["password", password]
    return (f"{shlex.join(cmd)} && {notify('Wi-Fi', f'Connected to {ssid}')}"
            f" || {notify('Wi-Fi', f'Could not connect to {ssid}')}")


class WifiMenu(Popup):
    def __init__(self):
        super().__init__("wifimenu", 260)
        on = wifi_enabled()
        self.add_switch("Wi-Fi", on, self.toggle)
        if not on:
            return
        self.add_sep()
        saved = saved_networks()
        nets = networks()
        if not nets:
            self.add_label("No networks found")
        for ssid, (active, sig, sec) in nets:
            secure = sec not in ("", "--")
            text = f"{CHECK if active else ' '} {ssid}{' ' + LOCK if secure else ''}  {sig}%"
            self.add_item(text, lambda s=ssid, a=active, sec=secure: self.pick(s, a, sec, saved))
        self.add_sep()
        self.add_item("Rescan", self.rescan, dim=True)

    def toggle(self, state):
        if state:
            run_bg(f"nmcli radio wifi on; sleep 4; {relaunch_cmd()}")
        else:
            run_bg("nmcli radio wifi off")
        self.destroy()

    def pick(self, ssid, active, secure, saved):
        if active:
            run_bg(f"{shlex.join(['nmcli', 'connection', 'down', 'id', ssid])}"
                   f" && {notify('Wi-Fi', f'Disconnected from {ssid}')}")
        elif ssid in saved or not secure:
            run_bg(connect_cmd(ssid))
        else:
            run_bg(relaunch_cmd("--password", ssid))
        self.destroy()

    def rescan(self):
        run_bg(f"nmcli dev wifi list --rescan yes >/dev/null; {relaunch_cmd()}")
        self.destroy()


class PasswordBox(Popup):
    def __init__(self, ssid):
        super().__init__("wifimenu", 260)
        self.ssid = ssid
        self.add_label(f"Password for {ssid}", dim=False)
        self.add_entry("password", self.submit)

    def submit(self, pw):
        run_bg(connect_cmd(self.ssid, pw))
        self.destroy()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--password":
        PasswordBox(sys.argv[2]).run()
    else:
        WifiMenu().run()
