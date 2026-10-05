#!/usr/bin/env bash
# Set up this Qtile (Wayland) desktop on a fresh Fedora install.
#
#   git clone https://github.com/FerrumLucis1/qtile ~/qtile
#   ~/qtile/install.sh              # do everything
#   ~/qtile/install.sh --dry-run    # only show what would happen
#   ~/qtile/install.sh --links-only # skip packages, just (re)link the config files
#
# Safe to run again: packages already installed are skipped, and existing config
# files are moved aside to <name>.bak-<date> before being replaced by links.
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
DRY=0
LINKS_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY=1 ;;
        --links-only) LINKS_ONLY=1 ;;
        -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

if [ "$(id -u)" -eq 0 ]; then
    echo "Run this as your normal user (it uses sudo where needed), not as root." >&2
    exit 1
fi

say() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
run() { echo "+ $*"; if [ "$DRY" -eq 0 ]; then "$@"; fi; }

PACKAGES=(
    # window manager + login
    qtile qtile-wayland sddm
    # bar widgets and pop-up menus
    python3-gobject gtk3 python3-psutil python3-dbus-fast python3-mypy
    # system pieces the bar talks to
    wireplumber NetworkManager bluez iw util-linux brightnessctl wlr-randr
    tuned tuned-ppd gnome-keyring gnome-keyring-pam
    # desktop apps and helpers
    alacritty fuzzel mako libnotify swaybg lxpolkit
    grim slurp wl-clipboard swaylock swayidle
    # config management
    git gh
)

install_packages() {
    say "Installing packages"
    run sudo dnf install -y --skip-unavailable "${PACKAGES[@]}"

    say "Brave browser"
    if rpm -q brave-browser >/dev/null 2>&1; then
        echo "already installed"
    else
        run sudo dnf install -y dnf-plugins-core
        run sudo dnf config-manager addrepo --overwrite \
            --from-repofile=https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo
        run sudo dnf install -y brave-browser
    fi

    say "JetBrainsMono Nerd Font"
    if fc-list | grep -q "JetBrainsMono Nerd Font"; then
        echo "already installed"
    else
        local dest="$HOME/.local/share/fonts/JetBrainsMonoNerd"
        run mkdir -p "$dest"
        if [ "$DRY" -eq 0 ]; then
            curl -fsSL https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.tar.xz \
                | tar -xJ -C "$dest"
        else
            echo "+ download JetBrainsMono.tar.xz into $dest"
        fi
        run fc-cache -f "$dest"
    fi
}

link() {  # link <file in repo> <target path>
    local src="$REPO/$1" dst="$2"
    if [ "$(readlink -f "$dst" 2>/dev/null)" = "$src" ]; then
        echo "ok      $dst"
        return
    fi
    run mkdir -p "$(dirname "$dst")"
    if [ -e "$dst" ] || [ -L "$dst" ]; then
        run mv "$dst" "$dst.bak-$(date +%Y%m%d-%H%M%S)"
    fi
    run ln -s "$src" "$dst"
}

link_configs() {
    say "Linking config files to $REPO"
    link config.py              "$HOME/.config/qtile/config.py"
    link autostart.sh           "$HOME/.config/qtile/autostart.sh"
    link alacritty/alacritty.toml "$HOME/.config/alacritty/alacritty.toml"
    link fuzzel/fuzzel.ini      "$HOME/.config/fuzzel/fuzzel.ini"
    link mako/config            "$HOME/.config/mako/config"
    link swaylock/config        "$HOME/.config/swaylock/config"
}

system_setup() {
    say "Login session"
    if grep -qs "qtile start -b wayland" /usr/share/wayland-sessions/*.desktop; then
        echo "Qtile (Wayland) session already present"
    elif [ "$DRY" -eq 1 ]; then
        echo "+ create /usr/share/wayland-sessions/qtile-wayland.desktop"
    else
        printf '%s\n' "[Desktop Entry]" "Name=Qtile (Wayland)" "Comment=Qtile on Wayland" \
            "Exec=qtile start -b wayland" "Type=Application" \
            | sudo tee /usr/share/wayland-sessions/qtile-wayland.desktop >/dev/null
        echo "created /usr/share/wayland-sessions/qtile-wayland.desktop"
    fi

    say "Display manager"
    if systemctl is-enabled display-manager.service >/dev/null 2>&1; then
        echo "a display manager is already enabled ($(readlink -f /etc/systemd/system/display-manager.service | xargs basename)) - leaving it"
    else
        run sudo systemctl enable sddm
        run sudo systemctl set-default graphical.target
    fi

    say "Power"
    run sudo systemctl enable --now tuned
    run sudo tuned-adm profile powersave
}

if [ "$LINKS_ONLY" -eq 0 ]; then
    install_packages
fi
link_configs
if [ "$LINKS_ONLY" -eq 0 ]; then
    system_setup
fi

say "Checking the Qtile config"
if [ "$DRY" -eq 0 ] && command -v qtile >/dev/null; then
    qtile check || true
fi

say "Done"
cat <<EOF
Next steps:
  - Log out (or reboot) and pick "Qtile (Wayland)" at the login screen.
  - Press Super+/ for the list of keyboard shortcuts.
  - Run: gh auth login   (so you can push config changes)
EOF
