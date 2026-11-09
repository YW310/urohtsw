#!/usr/bin/env bash
set -euo pipefail
bundle_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
target="${1:-$HOME/OHT_offline}"
data_dir="${2:-$target/data}"
if [[ "$(uname -m)" != x86_64 ]]; then echo 'Requires Linux x86_64'; exit 1; fi
if [[ -e "$target" ]]; then echo "Refusing to overwrite existing installation: $target"; exit 1; fi
command -v python3 >/dev/null
cd "$bundle_dir"
sha256sum -c SHA256SUMS
python3 - "$target" "$bundle_dir/inventory/package.json" <<'PYCODE'
import json,shutil,sys
from pathlib import Path
p=Path(sys.argv[1]).expanduser().absolute()
while not p.exists():p=p.parent
required=json.loads(Path(sys.argv[2]).read_text())['unpacked_bytes']+2*1024**3
available=shutil.disk_usage(p).free
if available<required:raise SystemExit(f'Insufficient disk space: need {required/1024**3:.1f} GiB, have {available/1024**3:.1f} GiB')
PYCODE
mkdir -p "$target"
for volume in oht_core.tar.gz oht_policy_runtime.tar.gz oht_T42_20000.tar.gz; do
  echo "Extracting $volume"
  tar --no-same-owner -xzf "$volume" -C "$target"
done
cp -a tools "$target/"
cp -a docs "$target/"
cp -a inventory "$target/"
cp -a udev "$target/"
cp -a launchers/. "$target/"
python3 "$target/tools/relocate.py" "$target" --data-dir "$data_dir"
printf '\nInstalled. Next: bash "%s/check_environment.sh"\n' "$target"
