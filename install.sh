#!/usr/bin/env bash
# Set up this Qtile (Wayland) desktop. Works on both machines:
#   - Fedora laptop        (dnf, battery, Qtile is the only desktop)
#   - CachyOS/Arch desktop (pacman, no battery, KDE Plasma installed alongside)
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
        -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

if [ "$(id -u)" -eq 0 ]; then
    echo "Run this as your normal user (it uses sudo where needed), not as root." >&2
    exit 1
fi

say() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
skip() { printf '\033[0;33mskipped:\033[0m %s\n' "$*"; }
run() { echo "+ $*"; if [ "$DRY" -eq 0 ]; then "$@"; fi; }

# ---------------------------------------------------------------- what machine is this?
. /etc/os-release
case " ${ID:-} ${ID_LIKE:-} " in
    *" fedora "*) DISTRO=fedora ;;
    *" arch "*)   DISTRO=arch ;;
    *) echo "Unsupported system ($PRETTY_NAME) - only Fedora and Arch-based (CachyOS) are handled." >&2
       echo "You can still link the config files with: $0 --links-only" >&2
       [ "$LINKS_ONLY" -eq 1 ] || exit 1
       DISTRO=other ;;
esac

if ls -d /sys/class/power_supply/BAT* >/dev/null 2>&1; then MACHINE=laptop; else MACHINE=desktop; fi

# KDE Plasma installed too? Then leave the things both desktops share alone
# (login screen theme, GTK settings file, default apps).
PLASMA=0
if ls /usr/share/wayland-sessions/plasma*.desktop /usr/share/xsessions/plasma*.desktop >/dev/null 2>&1; then
    PLASMA=1
fi

say "Detected: $PRETTY_NAME, $MACHINE$([ "$PLASMA" -eq 1 ] && echo ", KDE Plasma also installed")"

# ---------------------------------------------------------------- packages
FEDORA_PACKAGES=(
    # window manager + login
    qtile qtile-wayland sddm
    # bar widgets and pop-up menus
    python3-gobject gtk3 python3-psutil python3-dbus-fast python3-mypy
    # system pieces the bar talks to
    wireplumber NetworkManager bluez iw util-linux wlr-randr
    gnome-keyring gnome-keyring-pam
    # desktop apps and helpers
    alacritty fuzzel mako libnotify lxpolkit
    grim slurp wl-clipboard swaylock swayidle
    thunar tumbler ristretto
    # config management
    git gh
)
FEDORA_LAPTOP=(brightnessctl tuned tuned-ppd)

ARCH_PACKAGES=(
    # window manager + login (xwayland lets X11-only apps like Steam run inside Qtile)
    qtile xorg-xwayland sddm
    # bar widgets and pop-up menus
    python-gobject gtk3 python-psutil python-dbus-fast mypy
    # system pieces the bar talks to
    wireplumber networkmanager bluez bluez-utils iw util-linux wlr-randr gnome-keyring
    # desktop apps and helpers
    alacritty fuzzel mako libnotify
    grim slurp wl-clipboard swaylock swayidle
    thunar tumbler ristretto
    ttf-jetbrains-mono-nerd
    # config management
    git github-cli
)
ARCH_LAPTOP=(brightnessctl)
# password pop-ups: KDE already ships an agent; otherwise use GNOME's
ARCH_NO_PLASMA=(polkit-gnome)

install_fedora() {
    local pkgs=("${FEDORA_PACKAGES[@]}")
    [ "$MACHINE" = laptop ] && pkgs+=("${FEDORA_LAPTOP[@]}")
    say "Installing packages (dnf)"
    run sudo dnf install -y --skip-unavailable "${pkgs[@]}"

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

install_arch() {
    local wanted=("${ARCH_PACKAGES[@]}") pkgs=() p
    [ "$MACHINE" = laptop ] && wanted+=("${ARCH_LAPTOP[@]}")
    [ "$PLASMA" -eq 0 ] && wanted+=("${ARCH_NO_PLASMA[@]}")
    say "Installing packages (pacman)"
    # pacman refuses the whole list if one name is unknown, so check each first
    for p in "${wanted[@]}"; do
        if pacman -Si "$p" >/dev/null 2>&1 || pacman -Qi "$p" >/dev/null 2>&1; then
            pkgs+=("$p")
        else
            skip "$p (not in the repos)"
        fi
    done
    # -Syu, not -S: Arch doesn't support partial upgrades - installing new packages
    # without updating everything else can leave KDE needing a newer Qt than is installed
    run sudo pacman -Syu --needed --noconfirm "${pkgs[@]}"
    if ! command -v brave >/dev/null; then
        skip "Brave browser - on CachyOS install it with: paru -S brave-bin"
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
    if [ "$PLASMA" -eq 1 ]; then
        skip "~/.config/gtk-3.0/settings.ini - KDE manages that file (System Settings > Appearance)"
    else
        link gtk-3.0/settings.ini "$HOME/.config/gtk-3.0/settings.ini"
    fi
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

    say "Login screen picture"
    if [ "$PLASMA" -eq 1 ]; then
        skip "the login screen is shared with KDE - keeping its theme"
    elif [ "$DISTRO" != fedora ]; then
        skip "set-login.sh is Fedora-only"
    elif ls "$REPO"/wallpapers/login.* >/dev/null 2>&1; then
        run "$REPO/set-login.sh" --yes
    else
        echo "no wallpapers/login.jpg - keeping the plain login screen"
    fi

    say "Default apps"
    if [ "$PLASMA" -eq 1 ]; then
        skip "KDE's defaults (Dolphin, Gwenview) are shared with Qtile - left as they are"
    else
        run xdg-mime default thunar.desktop inode/directory
        run xdg-mime default org.xfce.ristretto.desktop image/png image/jpeg image/gif image/webp image/bmp image/tiff
    fi

    say "Power"
    if [ "$DISTRO" = fedora ] && [ "$MACHINE" = laptop ]; then
        run sudo systemctl enable --now tuned
        run sudo tuned-adm profile powersave
    else
        skip "power-saving profile is for the Fedora laptop only"
    fi
}

if [ "$LINKS_ONLY" -eq 0 ]; then
    case "$DISTRO" in
        fedora) install_fedora ;;
        arch)   install_arch ;;
    esac
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
  - Log out (or reboot). On the login screen, click the session menu in the
    bottom-left corner and pick "Qtile (Wayland)".$([ "$PLASMA" -eq 1 ] && printf '\n    To go back to KDE, log out and pick "Plasma (Wayland)" there.')
  - Press Super+/ for the list of keyboard shortcuts.
  - Run: gh auth login   (so you can push config changes)
EOF
