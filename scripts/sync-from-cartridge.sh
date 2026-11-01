#!/bin/sh
# Pull the latest plugin_commerce_client (main) and refresh the theme app extension from it:
#   assets/cimulate-init.js, commerceClient.css, commerce-client-icon.svg (copied as-is, one guard patched in)
#   blocks/shopper_agent.liquid: default of the "cdn_version" setting <- DEFAULT_CDN_VERSION in configHelper.js
#   blocks/shopper_agent.liquid: "assets synced from" comment <- cartridge commit
# usage: scripts/sync-from-cartridge.sh [path-to-plugin_commerce_client clone]   (default ~/src/plugin_commerce_client)
set -eu
SRC=${1:-$HOME/src/plugin_commerce_client}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
EXT="$ROOT/extensions/shopper-agent-widget"
C="$SRC/cartridges/plugin_commerce_client/cartridge"

git -C "$SRC" pull --ff-only -q
COMMIT=$(git -C "$SRC" log -1 --format='%h %cs')
CDN=$(sed -n "s/^var DEFAULT_CDN_VERSION = '\(.*\)';/\1/p" "$C/scripts/cimulate/configHelper.js")
[ -n "$CDN" ] || { echo "DEFAULT_CDN_VERSION not found" >&2; exit 1; }

cp "$C/static/default/css/commerceClient.css" "$EXT/assets/"
cp "$C/static/default/images/commerce-client-icon.svg" "$EXT/assets/"

# Shopify has no CommerceClient-GetPrechatConfig endpoint: skip the prechat handshake when
# data-prechat-url is empty (same guard the cartridge already uses for UpdateECOMSession).
# Pre-chat values are rendered by Liquid into data-routing-attributes instead.
ANCHOR="            var csrfToken = widgetConfig.prechatCsrfToken;

            function body() {"
python3 -I - "$C/static/default/js/cimulate-init.js" "$EXT/assets/cimulate-init.js" "$ANCHOR" <<'EOF'
import sys
src, dst, anchor = sys.argv[1:]
s = open(src).read()
assert s.count(anchor) == 1, 'prechat anchor changed upstream; re-check the patch'
s = s.replace(anchor, anchor.replace('\n\n', '\n\n            if (!PRECHAT_URL) {\n                return;\n            }\n\n', 1))
open(dst, 'w').write(s)
EOF

python3 -I - "$EXT/blocks/shopper_agent.liquid" "$CDN" "$COMMIT" <<'EOF'
import re, sys
path, cdn, commit = sys.argv[1:]
s = open(path).read()
pat = r'("id": "cdn_version",\s*"label": "[^"]*",\s*"default": ")[^"]*(")'
assert len(re.findall(pat, s)) == 1, 'cdn_version setting not found in block schema'
s = re.sub(pat, r'\g<1>' + cdn + r'\g<2>', s)
src = r'(\{%- comment -%\} assets synced from: )[^{]*(\{%- endcomment -%\})'
assert len(re.findall(src, s)) == 1, 'source comment not found in block'
open(path, 'w').write(re.sub(src, r'\g<1>plugin_commerce_client ' + commit + ', widget ' + cdn + r' \g<2>', s))
EOF

echo "synced plugin_commerce_client $COMMIT, widget $CDN"
