#!/bin/bash
SRC="$HOME/Swaytastic"

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

cp $SRC/zshrc $HOME/.zshrc
cp $SRC/zprofile $HOME/.zprofile

cp -a $SRC/config/* $HOME/.config/
sudo cp -a $SRC/local/colors/Swaytastic.conf /usr/share/qt6ct/colors/
sudo cp -a $SRC/local/qss/Swaytastic.qss /usr/share/qt6ct/qss/
sudo cp -a $SRC/local/themes/Swaytastic /usr/share/themes/
sudo cp -a $SRC/local/icons/Swaytastic /usr/share/icons/

gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
gsettings set org.gnome.desktop.interface gtk-theme 'Swaytastic'
gsettings set org.gnome.desktop.interface icon-theme 'Swaytastic'
