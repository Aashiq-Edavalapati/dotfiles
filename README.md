# My Linux Configurations

This repository contains configuration files for my personal Linux environment.

The setup is based on **Arch Linux with Wayland** and focuses on a minimal, fast, and keyboard-driven workflow.

## Environment

* **Window Manager:** Hyprland
* **Shell:** Fish
* **Terminal:** Foot
* **Status / utilities:** Fastfetch, Btop, Htop
* **Launcher:** Fuzzel
* **Dock:** nwg-dock-hyprland
* **Prompt:** Starship

## Key Configurations

| Tool                  | Path                   |
| --------------------- | ---------------------- |
| Hyprland              | `hypr/`                |
| Terminal (Foot)       | `foot/`                |
| Shell (Fish)          | `fish/`                |
| Launcher (Fuzzel)     | `fuzzel/`              |
| GTK Theme             | `gtk-3.0/`, `gtk-4.0/` |
| Starship Prompt       | `starship.toml`        |
| Systemd User Services | `systemd/user/`        |

## Notes

Only **actual configuration files** are tracked in this repository.
Cache files, runtime data, and application state are ignored using `.gitignore`.

## System

* OS: Arch Linux
* Display Server: Wayland
* WM: Hyprland
