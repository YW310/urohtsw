#!/usr/bin/env bash
# Optional, explicit administrator action on TARGET only. No motion.
set -euo pipefail
root_dir="$(cd -- "$(dirname -- "$0")/.." && pwd)"
if [[ ${EUID} -ne 0 ]]; then echo "Run with sudo on target only: sudo bash $0 USERNAME"; exit 1; fi
operator="${1:?Specify the desktop login username}"
id "$operator" >/dev/null
backup_dir="/etc/udev/rules.d/oht-backup-$(date +%Y%m%dT%H%M%S)"
mkdir -p "$backup_dir"
for f in "$root_dir"/udev/*.rules; do
 name="$(basename -- "$f")"
 if [[ -f "/etc/udev/rules.d/$name" ]]; then cp -a "/etc/udev/rules.d/$name" "$backup_dir/"; fi
 install -m 0644 "$f" "/etc/udev/rules.d/$name"
done
usermod -aG dialout,video,plugdev "$operator"
udevadm control --reload-rules
printf 'USB rules installed. Log out/in, then reconnect cameras while capture is stopped. Backup: %s\n' "$backup_dir"
