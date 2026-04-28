#!/bin/bash
#
# verify_kernel.sh — integrity guard for the four protected kernel files.
#
# The kernel (CLAUDE.md, accuracy-protocol.md, skill-architecture-standards.md,
# analyst-profile.md) defines universal rules. CLAUDE.md says they must NEVER
# be modified by sessions or skills. Until now that was enforced by reminding
# the model. This script enforces it at the filesystem layer:
#
#   - Kernel files are chmod 444 (read-only) by default
#   - SHA-256 checksums are stored in scripts/kernel-checksums.txt
#   - Verification fires on session-start; drift sends a notification
#
# Usage:
#   verify_kernel.sh             Verify checksums (default). Exit 0 = clean, 1 = drift.
#   verify_kernel.sh --update    Regenerate baseline (only after authorized kernel edit).
#   verify_kernel.sh --lock      chmod 444 on all kernel files (re-protect).
#   verify_kernel.sh --unlock    chmod 644 on all kernel files (allow editing).
#   verify_kernel.sh --status    Show chmod state and checksum state.
#
# Authorized-edit workflow:
#   ./scripts/verify_kernel.sh --unlock
#   <edit a kernel file>
#   ./scripts/verify_kernel.sh --update     (regenerates checksums AND re-locks)
#
set -u
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECKSUMS_FILE="$REPO_ROOT/scripts/kernel-checksums.txt"

KERNEL_FILES=(
  "CLAUDE.md"
  "shared-context/accuracy-protocol.md"
  "shared-context/skill-architecture-standards.md"
  "shared-context/analyst-profile.md"
  "shared-context/copywriting-rules.md"
)

cd "$REPO_ROOT" || { echo "ERROR: cannot cd to $REPO_ROOT"; exit 2; }

notify() {
  /usr/bin/osascript -e "display notification \"$2\" with title \"$1\" sound name \"Basso\"" >/dev/null 2>&1 || true
}

cmd_lock() {
  /bin/chmod 444 "${KERNEL_FILES[@]}"
  echo "✓ Kernel locked (chmod 444):"
  /bin/ls -l "${KERNEL_FILES[@]}" | /usr/bin/awk '{print "  ", $1, $NF}'
}

cmd_unlock() {
  /bin/chmod 644 "${KERNEL_FILES[@]}"
  echo "✓ Kernel unlocked (chmod 644). Edit, then run --update to regenerate baseline AND re-lock."
}

cmd_update() {
  /bin/chmod 644 "${KERNEL_FILES[@]}" 2>/dev/null
  /usr/bin/shasum -a 256 "${KERNEL_FILES[@]}" > "$CHECKSUMS_FILE"
  /bin/chmod 444 "${KERNEL_FILES[@]}"
  echo "✓ Baseline checksums regenerated and kernel re-locked:"
  /bin/cat "$CHECKSUMS_FILE"
}

cmd_status() {
  echo "Kernel file permissions:"
  /bin/ls -l "${KERNEL_FILES[@]}" | /usr/bin/awk '{print "  ", $1, $NF}'
  echo
  if [ -f "$CHECKSUMS_FILE" ]; then
    echo "Stored checksums ($CHECKSUMS_FILE):"
    /bin/cat "$CHECKSUMS_FILE" | /usr/bin/awk '{print "  ", $0}'
  else
    echo "No baseline checksums file found at $CHECKSUMS_FILE"
  fi
}

cmd_verify() {
  if [ ! -f "$CHECKSUMS_FILE" ]; then
    echo "ERROR: No baseline checksums at $CHECKSUMS_FILE"
    echo "Run with --update to generate baseline."
    exit 2
  fi

  if /usr/bin/shasum -a 256 -c "$CHECKSUMS_FILE" --status; then
    local n=${#KERNEL_FILES[@]}
    echo "✓ Kernel integrity verified ($n/$n files match baseline)"
    exit 0
  else
    echo "✗ KERNEL DRIFT DETECTED"
    /usr/bin/shasum -a 256 -c "$CHECKSUMS_FILE" 2>&1 | /usr/bin/grep -v ': OK$'
    notify "Kernel Integrity — DRIFT" "Kernel files have changed unexpectedly. Review and run scripts/verify_kernel.sh --update only if the change is authorized."
    exit 1
  fi
}

case "${1:-verify}" in
  --update)  cmd_update ;;
  --lock)    cmd_lock ;;
  --unlock)  cmd_unlock ;;
  --status)  cmd_status ;;
  verify|"") cmd_verify ;;
  *)
    echo "Usage: $0 [verify|--update|--lock|--unlock|--status]"
    exit 2
    ;;
esac
