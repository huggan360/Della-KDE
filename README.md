# Della KDE

Della is a glassmorphism theme for KDE Plasma 6 on Arch Linux. It includes the Plasma theme, Kvantum theme, KDE window decoration, Liquid Glass effect, colors, wallpaper, and panel layout.

## Install on Arch Linux

Install the build and KDE dependencies:

```sh
sudo pacman -S --needed base-devel cmake extra-cmake-modules git kconfig kcoreaddons kdecoration kglobalaccel kiconthemes knewstuff kpackage kwayland kwindowsystem qt6-base qt6-declarative qt6-tools qt6-wayland kvantum
```

Clone and install Della for the current user:

```sh
git clone https://github.com/huggan360/Della-KDE.git
cd Della-KDE
python3 install.py
```

Use `python3 install.py --light` for the light preset. The installer writes only to the current user’s KDE directories and creates a backup before changing settings. Log out and back in once after the first install so KWin and Qt plugins load completely.

To update an existing installation:

```sh
cd ~/della-kde
git pull
python3 install.py
```

To restore the first pre-Della backup:

```sh
python3 restore.py
```

The theme is designed for Arch Linux, KDE Plasma 6, and Wayland. The decoration and compositor effect compile against the KDE and Qt versions installed on the target computer.
