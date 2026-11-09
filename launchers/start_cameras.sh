#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
exec "$OHT_ROOT/home/samsung/.gello_python311/bin/python" -B "$OHT_ROOT/tools/services.py" cameras
