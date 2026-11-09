#!/usr/bin/env bash
set -euo pipefail
manual_root="$(cd -- "$(dirname -- "$0")" && pwd)"
exec xdg-open "$manual_root/docs/index.html"
