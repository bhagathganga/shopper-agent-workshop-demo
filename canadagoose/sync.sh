#!/bin/sh
# Pull the latest plugin_commerce_client and refresh vendor/ from it:
#   cimulate-init.js, commerceClient.css, commerce-client-icon.svg (copied as-is, one guard patched in)
#   version.js  (DEFAULT_CDN_VERSION from configHelper.js + source commit)
# usage: ./sync.sh [path-to-plugin_commerce_client clone]   (default ~/src/plugin_commerce_client)
set -eu
SRC=${1:-$HOME/src/plugin_commerce_client}
HERE=$(cd "$(dirname "$0")" && pwd)
C="$SRC/cartridges/plugin_commerce_client/cartridge"

git -C "$SRC" pull --ff-only -q
COMMIT=$(git -C "$SRC" log -1 --format='%h %cs')
CDN=$(sed -n "s/^var DEFAULT_CDN_VERSION = '\(.*\)';/\1/p" "$C/scripts/cimulate/configHelper.js")
[ -n "$CDN" ] || { echo "DEFAULT_CDN_VERSION not found" >&2; exit 1; }

mkdir -p "$HERE/vendor"
cp "$C/static/default/css/commerceClient.css" "$HERE/vendor/"
cp "$C/static/default/images/commerce-client-icon.svg" "$HERE/vendor/"

# No SFCC here, so there is no CommerceClient-GetPrechatConfig endpoint: skip the prechat
# handshake when data-prechat-url is empty (same guard the cartridge already uses for
# UpdateECOMSession). Pre-chat values go in data-routing-attributes instead.
ANCHOR="            var csrfToken = widgetConfig.prechatCsrfToken;

            function body() {"
python3 -I - "$C/static/default/js/cimulate-init.js" "$HERE/vendor/cimulate-init.js" "$ANCHOR" <<'EOF'
import sys
src, dst, anchor = sys.argv[1:]
s = open(src).read()
assert s.count(anchor) == 1, 'prechat anchor changed upstream; re-check the patch'
s = s.replace(anchor, anchor.replace('\n\n', '\n\n            if (!PRECHAT_URL) {\n                return;\n            }\n\n', 1))
open(dst, 'w').write(s)
EOF

printf 'window.CC_CDN_VERSION = "%s";\nwindow.CC_SOURCE = "plugin_commerce_client %s";\n' "$CDN" "$COMMIT" > "$HERE/vendor/version.js"
echo "synced plugin_commerce_client $COMMIT, widget $CDN"
