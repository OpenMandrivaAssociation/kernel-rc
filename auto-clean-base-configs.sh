#!/bin/bash
# OpenMandriva kernel config maintenance wrapper.
# Prefer: ./manage-kernel-configs.py --help
#
# Usage:
#   ./auto-clean-base-configs.sh              # strip dups + extract common
#   ./auto-clean-base-configs.sh stats
#   ./auto-clean-base-configs.sh strip-duplicates
#   ./auto-clean-base-configs.sh extract-common
#   ./auto-clean-base-configs.sh verify [outdir]

set -e
cd "$(dirname "$0")"
cmd="${1:-all}"
shift || true

case "$cmd" in
  stats) exec python3 ./manage-kernel-configs.py stats "$@" ;;
  strip-duplicates|strip-noise) exec python3 ./manage-kernel-configs.py "$cmd" "$@" ;;
  extract-common) exec python3 ./manage-kernel-configs.py extract-common "$@" ;;
  verify) exec python3 ./manage-kernel-configs.py verify --outdir "${1:-config-verify/out}" ${2:+--arches "$2"} ;;
  all)
    python3 ./manage-kernel-configs.py extract-common
    python3 ./manage-kernel-configs.py stats
    ;;
  *)
    echo "Unknown command: $cmd"
    echo "Use: stats | strip-duplicates | extract-common | verify | all"
    exit 1
    ;;
esac
