#!/usr/bin/env bash
# assemble.sh <renderDir> <score.wav|-> <outName> [posterTime]
# 120 fps chunks -> blend frame pairs (a 180-degree shutter's motion blur) -> 60 fps master with the score,
# plus a poster frame and a 720p30 web copy (small enough for a portfolio or landing page).
set -e
D="$(cd "$1" && pwd)"; WAV="$2"; NAME="$3"; FF="${FFMPEG:-ffmpeg}"
OUT="$(pwd)/$NAME"
read DUR FPS < <(python3 -c "import json;j=json.load(open('$D/film.json'));print(j['dur'],j['fps'])")
POSTER="${4:-$(python3 -c "print(max(0,$DUR-1.0))")}"
if [ "$FPS" = "120" ]; then VF="tmix=frames=2:weights='1 1',select='not(mod(n\,2))',setpts=N/60/TB,format=yuv420p"; else VF="format=yuv420p"; fi
ARGS=(-y -loglevel error -f concat -safe 0 -i "$D/chunks.txt")
if [ -f "$WAV" ]; then ARGS+=(-i "$(cd "$(dirname "$WAV")" && pwd)/$(basename "$WAV")"); fi
ARGS+=(-filter_complex "[0:v]$VF[v]" -map "[v]")
if [ -f "$WAV" ]; then ARGS+=(-map 1:a -c:a aac -b:a 256k); fi
ARGS+=(-r 60 -c:v libx264 -preset slow -crf 16 -profile:v high -tune film -movflags +faststart -t "$DUR" "$OUT.mp4")
$FF "${ARGS[@]}"
$FF -y -loglevel error -ss "$POSTER" -i "$OUT.mp4" -frames:v 1 -q:v 2 "$OUT-poster.jpg"
$FF -y -loglevel error -i "$OUT.mp4" -vf "scale=1280:-2:flags=lanczos" -r 30 -c:v libx264 -preset slow -crf 24 -profile:v high -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart "$OUT-web.mp4"
ls -la "$OUT.mp4" "$OUT-poster.jpg" "$OUT-web.mp4"
$FF -hide_banner -i "$OUT.mp4" 2>&1 | grep -E "Duration|Stream" || true
