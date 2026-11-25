#!/usr/bin/env bash
# Capture one 1280x720 spawn-camera frame of a native Screech build under Xvfb.
# Usage: scripts/capture-screenshot.sh <screech-bin> <out.png>
set -euo pipefail
BIN=${1:?screech binary}
OUT=${2:?output png}
WIDTH=1280
HEIGHT=720
WORK=$(mktemp -d)
DISPLAY_NUM=${DISPLAY_NUM:-103}
ICD=${VK_ICD_FILENAMES:-/usr/share/vulkan/icd.d/lvp_icd.json}

cleanup() {
  if [[ -n "${FFMPEG_PID:-}" ]]; then kill "$FFMPEG_PID" 2>/dev/null || true; wait "$FFMPEG_PID" 2>/dev/null || true; fi
  if [[ -n "${GAME_PID:-}" ]]; then kill "$GAME_PID" 2>/dev/null || true; fi
  if [[ -n "${XVFB_PID:-}" ]]; then kill "$XVFB_PID" 2>/dev/null || true; wait "$XVFB_PID" 2>/dev/null || true; fi
  rm -rf "$WORK"
}
trap cleanup EXIT

Xvfb ":$DISPLAY_NUM" -screen 0 ${WIDTH}x${HEIGHT}x24 -ac +extension GLX +render -noreset >/tmp/screech-xvfb.log 2>&1 &
XVFB_PID=$!
sleep 0.4

export DISPLAY=":$DISPLAY_NUM"
unset WAYLAND_DISPLAY || true
export WINIT_UNIX_BACKEND=x11
export VK_ICD_FILENAMES="$ICD"

# Record the whole session so we can pick a frame before the window closes.
ffmpeg -y -f x11grab -draw_mouse 0 -video_size ${WIDTH}x${HEIGHT} -framerate 15 -i "$DISPLAY" \
  -c:v libx264 -pix_fmt yuv420p -preset ultrafast -tune zerolatency \
  "$WORK/session.mp4" >/tmp/screech-ffmpeg.log 2>&1 &
FFMPEG_PID=$!
sleep 0.3

RUST_LOG=${RUST_LOG:-info} "$BIN" --screenshot "$OUT"
GAME_STATUS=$?

# Flush the encoder, then grab a frame from just before the window disappeared.
sleep 0.4
kill -INT "$FFMPEG_PID" 2>/dev/null || true
wait "$FFMPEG_PID" 2>/dev/null || true
FFMPEG_PID=

if [[ ! -s "$WORK/session.mp4" ]]; then
  echo "capture failed: no video written" >&2
  cat /tmp/screech-ffmpeg.log >&2 || true
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
# Try 1.2s before the end, then 0.4s, then the last frame.
if ! ffmpeg -y -sseof -1.2 -i "$WORK/session.mp4" -frames:v 1 "$OUT" >/tmp/screech-ffmpeg-extract.log 2>&1; then
  ffmpeg -y -sseof -0.4 -i "$WORK/session.mp4" -frames:v 1 "$OUT" >/tmp/screech-ffmpeg-extract.log 2>&1 || \
  ffmpeg -y -i "$WORK/session.mp4" -update 1 "$OUT" >/tmp/screech-ffmpeg-extract.log 2>&1
fi

# Keep a copy of the session for debugging if the still is tiny / empty.
cp "$WORK/session.mp4" /tmp/screech-session.mp4
echo "wrote $OUT ($(wc -c < "$OUT") bytes), video $(wc -c < /tmp/screech-session.mp4) bytes, game exit $GAME_STATUS"
exit "$GAME_STATUS"
