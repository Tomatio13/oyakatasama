#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: executor_quiet.sh <command> [args...]" >&2
  exit 2
fi

executor_name="$1"
shift

# Resolve a writable log directory independent of the caller's working directory.
# TMPDIR may be unset, empty, or point at an unreadable/unwritable/non-existent
# path; fall back through /tmp, and finally to a private mktemp directory.
resolve_log_dir() {
  local candidate
  for candidate in "${TMPDIR:-}" "/tmp"; do
    if [ -n "$candidate" ] && [ -d "$candidate" ] && [ -w "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  mktemp -d 2>/dev/null || true
}

log_dir="$(resolve_log_dir)"
if [ -z "$log_dir" ]; then
  echo "executor_quiet.sh: no writable log directory available" >&2
  exit 2
fi

timestamp="$(date +%Y%m%d-%H%M%S)"
stdout_log="${log_dir}/${executor_name}-${timestamp}-$$.out.log"
stderr_log="${log_dir}/${executor_name}-${timestamp}-$$.err.log"

# Create the capture files up front with mode 600 (umask 077) so logs are never
# world-readable, even while the executor is still running. Truncating redirects
# below keep that mode intact.
( umask 077 && : >"$stdout_log" && : >"$stderr_log" )

set +e
"$executor_name" "$@" >"$stdout_log" 2>"$stderr_log"
status=$?
set -e

if [ "$status" -eq 0 ]; then
  rm -f -- "$stdout_log" "$stderr_log"
  exit 0
fi

chmod 600 "$stdout_log" "$stderr_log" 2>/dev/null || true
printf '%s failed (exit %s). stdout: %s stderr: %s\n' "$executor_name" "$status" "$stdout_log" "$stderr_log" >&2
exit "$status"
