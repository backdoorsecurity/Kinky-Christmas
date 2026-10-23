#!/bin/bash
SRC="$HOME/Kinky-Christmas"

export BARE_METAL=BARE_METAL
export VIRTUAL_MACHINE=VIRTUAL_MACHINE
export CONFIG_METAL=config_metal
export CONFIG_VM=config_vm

# Bare-metal package list. The guest list is VM_PACKAGES.
METAL_PACKAGES=(
  sway
  foot
  waybar
  pcmanfm-qt
  qt6ct
  adwaita-icon-theme
  grim
  brightnessctl
  wlsunset
  oxygencursors
  qt6-wayland
  qt6-qpa-plugins
  qt6-gtk-platformtheme
  qt6-svg-plugins
  brightness-udev
  zsh
  zsh-autosuggestions
  zsh-syntax-highlighting
  copyq
  wf-recorder
  wtype
  zram-tools
  lm-sensors
  curl
  unzip
  zip
  tree
  socat
  nmap
  traceroute
  pciutils
  usbutils
  locate
  build-essential
  network-manager
  network-manager-gnome
  pipewire
  pipewire-pulse
  wireplumber
  xdg-utils
  gnome-keyring
  libnotify-bin
  virt-manager
  qemu-system-x86
  dnsmasq
  swayimg
  celluloid
  firejail
  dosfstools
  adb
  smartmontools
  intel-media-va-driver
  mesa-vulkan-drivers
  aircrack-ng
  dkms
  ffmpeg
  git
  hydra
  libdrm-dev
  libegl-dev
  libepoxy-dev
  libgbm-dev
  libglvnd-dev
  libvirt-daemon
  lz4
  meson
  ninja-build
  pkg-config
  pulseaudio-utils
  python3-full
  python3-pip
  python3-venv
  python3-yaml
  python3.13-venv
  qemu-utils
  rfkill
  rsync
  sshpass
  virtiofsd
)

# Guest package list. Host-only names stay in PACKAGES.
VM_PACKAGES=(
  sway
  foot
  waybar
  pcmanfm-qt
  qt6ct
  adwaita-icon-theme
  grim
  oxygencursors
  qt6-wayland
  qt6-qpa-plugins
  qt6-gtk-platformtheme
  qt6-svg-plugins
  zsh
  zsh-autosuggestions
  zsh-syntax-highlighting
  copyq
  wf-recorder
  wtype
  zram-tools
  curl
  unzip
  zip
  tree
  socat
  nmap
  traceroute
  pciutils
  usbutils
  locate
  build-essential
  pipewire
  pipewire-pulse
  wireplumber
  xdg-utils
  gnome-keyring
  libnotify-bin
  swayimg
  celluloid
  dosfstools
  adb
  smartmontools
  intel-media-va-driver
  mesa-vulkan-drivers
  aircrack-ng
  dkms
  ffmpeg
  git
  hydra
  libdrm-dev
  libegl-dev
  libepoxy-dev
  libgbm-dev
  libglvnd-dev
  lz4
  meson
  ninja-build
  pkg-config
  pulseaudio-utils
  python3-full
  python3-pip
  python3-venv
  python3-yaml
  python3.13-venv
  rfkill
  rsync
  sshpass
  drm-info
  libnss3-tools
  openvpn
  xwayland
)

while true; do
  echo "Bare Metal or Virtual Machine?"
  echo "1 Bare Metal"
  echo "2 Virtual Machine"
  read -r -p "Operating System (): " OS_CHOICE
  if [ "$OS_CHOICE" = "1" ]; then
    echo "Operating System (Bare Metal)"
    export INSTALL_TARGET="$BARE_METAL"
    break
  elif [ "$OS_CHOICE" = "2" ]; then
    echo "Operating System (Virtual Machine)"
    export INSTALL_TARGET="$VIRTUAL_MACHINE"
    break
  else
    echo "Enter 1 or 2."
  fi
done

if [ "$INSTALL_TARGET" = "$BARE_METAL" ]; then
  INSTALL_PACKAGES=("${METAL_PACKAGES[@]}")
elif [ "$INSTALL_TARGET" = "$VIRTUAL_MACHINE" ]; then
  INSTALL_PACKAGES=("${VM_PACKAGES[@]}")
fi

echo "installing packages"
sudo apt update
sudo apt install -y --no-install-recommends "${INSTALL_PACKAGES[@]}"

echo "Install Brave Origin Nightly"
if command -v brave-origin-nightly >/dev/null 2>&1; then
  echo "    already installed"
else
  curl -fsS https://dl.brave.com/install.sh | FLAVOR=origin CHANNEL=nightly sh
fi

# installing ollama for speech to text.
#curl -fsSL https://ollama.com/install.sh | sh
#ollama pull frozenlab/qwen3-asr:1.7b
#ollama pull frozenlab/qwen3-asr:0.6b

cp $SRC/zshrc $HOME/.zshrc
cp $SRC/zprofile $HOME/.zprofile
mkdir -p $HOME/.config
if [ "$INSTALL_TARGET" = "$BARE_METAL" ]; then
  cp -a "$SRC/$CONFIG_METAL/"* $HOME/.config/
elif [ "$INSTALL_TARGET" = "$VIRTUAL_MACHINE" ]; then
  cp -a "$SRC/$CONFIG_VM/"* $HOME/.config/
fi
mkdir -p $HOME/.local/bin
cp -a $SRC/local/bin/* $HOME/.local/bin
sudo cp -a $SRC/usr_local/colors/Swaytastic.conf /usr/share/qt6ct/colors/
sudo cp -a $SRC/usr_local/qss/Swaytastic.qss $SRC/usr_local/qss/down.png $SRC/usr_local/qss/up.png $SRC/usr_local/qss/right.png /usr/share/qt6ct/qss/
sudo cp -a $SRC/usr_local/themes/Swaytastic /usr/share/themes/
sudo cp -a $SRC/usr_local/icons/Swaytastic /usr/share/icons/
sudo gtk-update-icon-cache -f /usr/share/icons/Swaytastic
# pcmanfm stores the wallpaper path literally; sway config expands $HOME itself
sed -i "s|\$HOME|$HOME|g" "$HOME/.config/pcmanfm-qt/sway/settings.conf"

# Menu launches do not go through the Sway keybinding, so give them qt6ct too.
# --qt-version=6 comes from brave-origin-nightly-flags.conf in the selected config dir.
mkdir -p "$HOME/.local/share/applications"
if [ -f /usr/share/applications/brave-origin-nightly.desktop ]; then
  sed "s|^Exec=/usr/bin/brave-origin-nightly|Exec=env QT_QPA_PLATFORMTHEME=qt6ct /usr/bin/brave-origin-nightly|" \
    /usr/share/applications/brave-origin-nightly.desktop > "$HOME/.local/share/applications/brave-origin-nightly.desktop"
fi
if [ -f /usr/share/applications/com.brave.Origin.nightly.desktop ]; then
  sed "s|^Exec=/usr/bin/brave-origin-nightly|Exec=env QT_QPA_PLATFORMTHEME=qt6ct /usr/bin/brave-origin-nightly|" \
    /usr/share/applications/com.brave.Origin.nightly.desktop > "$HOME/.local/share/applications/com.brave.Origin.nightly.desktop"
fi

gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
gsettings set org.gnome.desktop.interface gtk-theme 'Swaytastic'
gsettings set org.gnome.desktop.interface icon-theme 'Swaytastic'
