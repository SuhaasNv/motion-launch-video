#!/usr/bin/env bash
# sample.sh <video.mp4> <outDir> <t1,t2,...>  -> PNG frames from the finished encode (review what ships, not the page)
set -e; FF="${FFMPEG:-ffmpeg}"; mkdir -p "$2"
IFS=',' read -ra TS <<< "$3"
for t in "${TS[@]}"; do $FF -y -loglevel error -ss "$t" -i "$1" -frames:v 1 "$2/v$(printf '%06.2f' "$t").png"; done
echo "${#TS[@]} frames -> $2"
