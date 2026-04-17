#!/usr/bin/env bash
# Install qmd + marp-cli into the plugin's CLAUDE_PLUGIN_DATA directory.
# Fired by the SessionStart hook. Must never exit non-zero — a failing
# SessionStart hook would block Claude Code sessions from starting.

set +e

[ -z "${CLAUDE_PLUGIN_DATA}" ] && exit 0
[ -z "${CLAUDE_PLUGIN_ROOT}" ] && exit 0

DATA="${CLAUDE_PLUGIN_DATA}"
ROOT="${CLAUDE_PLUGIN_ROOT}"
VER_SRC="${ROOT}/scripts/deps-version.txt"
VER_DST="${DATA}/deps-version.txt"
SENTINEL="${DATA}/.deps-ok"

mkdir -p "${DATA}" 2>/dev/null || exit 0

# Already installed at the current version — skip
if [ -f "${SENTINEL}" ] && [ -f "${VER_DST}" ] && [ -f "${VER_SRC}" ]; then
  if diff -q "${VER_SRC}" "${VER_DST}" >/dev/null 2>&1; then
    exit 0
  fi
fi

echo "[ecogo-workflow] installing search and rendering dependencies..." >&2

cd "${DATA}" || exit 0
[ ! -f package.json ] && echo '{"private":true}' > package.json

if npm install @tobilu/qmd @marp-team/marp-cli 2>&1 | tail -5 >&2; then
  cp "${VER_SRC}" "${VER_DST}" 2>/dev/null
  touch "${SENTINEL}"
  echo "[ecogo-workflow] dependencies ready." >&2
else
  # Install failed — remove sentinel so next session retries. Do not fail the hook.
  rm -f "${SENTINEL}" "${VER_DST}" 2>/dev/null
  echo "[ecogo-workflow] dependency install failed; plugin will run without qmd/marp." >&2
fi

exit 0
