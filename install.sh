#!/bin/bash
SRC="$HOME/Kinky-Christmas"

PACKAGES=(
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
#  steam-installer
  dosfstools
  adb
  smartmontools
  intel-media-va-driver
  mesa-vulkan-drivers
)

echo "installing packages"
sudo apt update
sudo apt install -y --no-install-recommends "${PACKAGES[@]}"

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
cp -a $SRC/config/* $HOME/.config/
sudo cp -a $SRC/local/colors/Swaytastic.conf /usr/share/qt6ct/colors/
sudo cp -a $SRC/local/qss/Swaytastic.qss $SRC/local/qss/down.png $SRC/local/qss/up.png $SRC/local/qss/right.png /usr/share/qt6ct/qss/
sudo cp -a $SRC/local/themes/Swaytastic /usr/share/themes/
sudo cp -a $SRC/local/icons/Swaytastic /usr/share/icons/
sudo gtk-update-icon-cache -f /usr/share/icons/Swaytastic
# pcmanfm stores the wallpaper path literally; sway config expands $HOME itself
sed -i "s|\$HOME|$HOME|g" "$HOME/.config/pcmanfm-qt/sway/settings.conf"

# Menu launches do not go through the Sway keybinding, so give them qt6ct too.
# --qt-version=6 comes from config/brave-origin-nightly-flags.conf, copied above.
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
