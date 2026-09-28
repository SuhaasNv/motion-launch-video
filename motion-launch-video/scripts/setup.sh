#!/usr/bin/env bash
# Finds or installs what the pipeline needs, then prints export lines:
#   eval "$(bash <skill>/scripts/setup.sh <workdir>)"
# - ffmpeg with libx264 (system ffmpeg, else the static build from pip imageio-ffmpeg)
# - Chromium (CHROME_PATH already set, Playwright's cache, /opt/pw-browsers, or system chrome)
# - playwright-core in <workdir>/node_modules (no browser download)
# - numpy + scipy for the score
set -e
WORK="${1:-.}"; mkdir -p "$WORK"
log(){ echo "# $*" >&2; }
FF=""
if command -v ffmpeg >/dev/null && ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libx264; then FF=$(command -v ffmpeg); fi
if [ -z "$FF" ]; then
  python3 -c "import imageio_ffmpeg" 2>/dev/null || pip install -q imageio-ffmpeg >&2
  FF=$(python3 -c "import imageio_ffmpeg as i; print(i.get_ffmpeg_exe())")
fi
log "ffmpeg: $FF"
CH="${CHROME_PATH:-}"
if [ -z "$CH" ]; then
  for c in /opt/pw-browsers/chromium-*/chrome-linux/chrome "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux/chrome \
           "$HOME/Library/Caches/ms-playwright"/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium \
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" "$(command -v google-chrome || true)" "$(command -v chromium || true)"; do
    [ -n "$c" ] && [ -x "$c" ] && CH="$c" && break
  done
fi
[ -z "$CH" ] && log "no Chromium found: run 'npx playwright install chromium' or set CHROME_PATH" || log "chrome: $CH"
if [ ! -d "$WORK/node_modules/playwright-core" ]; then
  (cd "$WORK" && [ -f package.json ] || (cd "$WORK" && npm init -y >/dev/null)) 
  (cd "$WORK" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i -s playwright-core >&2)
fi
python3 -c "import numpy, scipy" 2>/dev/null || pip install -q numpy scipy >&2
echo "export FFMPEG='$FF'"
[ -n "$CH" ] && echo "export CHROME_PATH='$CH'"
echo "export NODE_PATH='$(cd "$WORK" && pwd)/node_modules'"
