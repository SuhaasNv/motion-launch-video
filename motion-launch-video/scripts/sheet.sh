#!/usr/bin/env bash
# sheet.sh <dirOfPngs> <out.png> [cols=3]  -> one contact sheet (640x360 tiles) to review many frames in one image read
set -e; FF="${FFMPEG:-ffmpeg}"; C="${3:-3}"
n=$(ls "$1"/*.png | wc -l); rows=$(( (n + C - 1) / C ))
$FF -y -loglevel error -pattern_type glob -i "$1/*.png" -vf "scale=640:-2,tile=${C}x${rows}:padding=4:color=white" -frames:v 1 "$2"
echo "$2"
