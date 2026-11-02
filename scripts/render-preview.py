"""Render the app embed (blocks/shopper_agent.liquid) to static HTML pages with mock Shopify objects,
so the exact markup + assets the app ships can be tested outside Shopify (e.g. on GitHub Pages).

usage: .venv/bin/python -I scripts/render-preview.py <out-dir>      (needs: pip install 'python-liquid<2')
Writes <out-dir>/{index,fr-ca,us-customer,pdp}.html and <out-dir>/assets/*.
Approximates Shopify Liquid: asset_url -> assets/<file>, json/stylesheet_tag/url_encode reimplemented.
"""
import html, json, os, re, shutil, subprocess, sys
from urllib.parse import quote
from liquid import Environment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, "extensions", "shopper-agent-widget")
out = sys.argv[1]

block = open(os.path.join(EXT, "blocks", "shopper_agent.liquid")).read()
schema = json.loads(re.search(r"{% schema %}(.*){% endschema %}", block, re.S).group(1))
defaults = {s["id"]: s.get("default") for s in schema["settings"] if "id" in s}
body_tpl = re.sub(r"{% schema %}.*{% endschema %}", "", block, flags=re.S)
synced = re.search(r"assets synced from: ([^{]*)", block).group(1).strip()
commit = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%h"], capture_output=True, text=True).stdout.strip()

env = Environment()
env.add_filter("json", lambda v: json.dumps(v))
env.add_filter("asset_url", lambda v: "assets/" + v)
env.add_filter("stylesheet_tag", lambda v: '<link rel="stylesheet" href="%s" media="all">' % v)
env.add_filter("url_encode", lambda v: quote(str(v), safe=""))
LOCALES = {lang: json.load(open(os.path.join(EXT, "locales", f)))
           for lang, f in (("en", "en.default.json"), ("fr", "fr.json"))}
current = {"lang": "en"}
def t(key):
    node = LOCALES[current["lang"]]
    for part in key.split("."):
        node = node[part]
    return node
env.add_filter("t", t)
# Contact-menu links without a real default get placeholders so every option stays visible in the preview.
PREVIEW_SETTINGS = {k: "#" for k in ("text_url", "whatsapp_url", "facebook_url", "call_url") if not defaults.get(k)}
tpl = env.from_string(body_tpl)

CA = {"country": {"iso_code": "CA", "currency": {"iso_code": "CAD"}}}
US = {"country": {"iso_code": "US", "currency": {"iso_code": "USD"}}}
base = dict(request={"locale": {"iso_code": "en"}, "page_type": "index"}, localization=CA,
            cart={"currency": {"iso_code": "CAD"}}, customer=None, product=None)
PARKA = {"id": 7000000000001, "handle": "expedition-parka",
         "selected_or_first_available_variant": {"sku": "2051M"}}
pages = [
    ("index", "Guest · en_CA · CAD", {}, {}),
    ("fr-ca", "Invité · fr_CA · CAD", dict(request={"locale": {"iso_code": "fr-CA"}, "page_type": "index"}), {}),
    ("us-customer", "Signed-in customer · en_US · USD",
     dict(localization=US, cart={"currency": {"iso_code": "USD"}},
          customer={"first_name": "Test", "last_name": "Shopper", "email": "test.shopper@example.com",
                    "phone": "", "accepts_marketing": True}), {}),
    ("pdp", "Product page (handle sent as page context) · en_CA",
     dict(request={"locale": {"iso_code": "en"}, "page_type": "product"}, product=PARKA),
     {"enable_page_context": True, "pdp_id_source": "handle"}),
]

SHELL = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Canada Goose · Shopify app embed preview</title>
<style>
  body {{ margin: 0; font-family: Arial, sans-serif; color: #181818; background: #f6f6f4; }}
  header {{ background: #000; color: #fff; padding: 18px 24px; letter-spacing: .2em; font-weight: 700; }}
  main {{ max-width: 860px; margin: 32px auto; padding: 0 24px; line-height: 1.5; }}
  nav a {{ display: inline-block; margin: 0 8px 8px 0; padding: 6px 12px; border: 1px solid #181818;
          color: #181818; text-decoration: none; font-size: 14px; }}
  nav a.on {{ background: #181818; color: #fff; }}
  textarea {{ box-sizing: border-box; width: 100%; height: 260px; background: #fff; border: 1px solid #ddd;
             padding: 12px; font: 12px/1.5 Menlo, Consolas, monospace; }}
  #routing-error {{ color: #b00020; }}
  button {{ padding: 8px 14px; border: 0; background: #181818; color: #fff; cursor: pointer; }}
  small {{ color: #666; }}
</style>
</head>
<body>
<header>CANADA GOOSE</header>
<main>
  <h2>Shopify app embed preview</h2>
  <p>This page is <code>blocks/shopper_agent.liquid</code> rendered with mock Shopify objects for:
     <b>{label}</b>. Assets are the ones the app ships.</p>
  <nav>{nav}</nav>
  <p><button id="new-chat">Start a new chat</button>
     <small>Pre-chat values only apply to a new conversation, so start one after switching scenarios.</small></p>
  <h3>Pre-chat routing attributes</h3>
  <p><small>Edit the JSON, then apply: it replaces this page's data-routing-attributes and starts a new chat.
     Saved in this browser per scenario.</small></p>
  <textarea id="routing" spellcheck="false" aria-label="Pre-chat routing attributes (JSON)">{routing}</textarea>
  <p><button id="routing-apply">Apply and start a new chat</button>
     <button id="routing-reset">Reset to scenario defaults</button>
     <small id="routing-error" role="alert"></small></p>
  <p><small>App commit {commit} · assets synced from {synced}</small></p>
</main>
<script>
  var ROUTING_KEY = 'cgprev-routing-{slug}';
  function newChat() {{
    [sessionStorage, localStorage].forEach(function (s) {{
      Object.keys(s).forEach(function (k) {{ if (/cim|miaw|scrt|convers|messag|cc_/i.test(k)) s.removeItem(k); }});
    }});
    location.reload();
  }}
  document.getElementById('new-chat').onclick = newChat;
  document.getElementById('routing-apply').onclick = function () {{
    var box = document.getElementById('routing'), err = document.getElementById('routing-error');
    try {{
      var v = JSON.parse(box.value);
      if (!v || typeof v !== 'object' || Array.isArray(v)) throw new Error('must be a JSON object');
      localStorage.setItem(ROUTING_KEY, JSON.stringify(v));
      newChat();
    }} catch (e) {{ err.textContent = 'Invalid JSON: ' + e.message; }}
  }};
  document.getElementById('routing-reset').onclick = function () {{
    localStorage.removeItem(ROUTING_KEY);
    newChat();
  }};
</script>
<!-- ===== app embed output (target: body) ===== -->
{embed}
<script>
  // Runs before the deferred widget scripts, so a saved override is what the widget reads.
  (function () {{
    var saved = localStorage.getItem(ROUTING_KEY), el = document.getElementById('cimulate-messaging-widget');
    if (!saved || !el) return;
    el.setAttribute('data-routing-attributes', saved);
    document.getElementById('routing').value = JSON.stringify(JSON.parse(saved), null, 2);
  }})();
</script>
</body>
</html>
"""

os.makedirs(out, exist_ok=True)
shutil.copytree(os.path.join(EXT, "assets"), os.path.join(out, "assets"), dirs_exist_ok=True)
for slug, label, over, settings_over in pages:
    current["lang"] = "fr" if slug == "fr-ca" else "en"
    ctx = dict(base, **over, block={"settings": dict(defaults, **PREVIEW_SETTINGS, **settings_over)})
    embed = tpl.render(**ctx).strip()
    routing = re.search(r'data-routing-attributes="([^"]*)"', embed).group(1)
    routing = json.dumps(json.loads(html.unescape(routing)), indent=2)
    nav = "".join('<a href="%s.html"%s>%s</a>' % (s, ' class="on"' if s == slug else "", l)
                  for s, l, _, _ in pages)
    lang = "fr" if slug == "fr-ca" else "en"
    with open(os.path.join(out, slug + ".html"), "w") as f:
        f.write(SHELL.format(slug=slug, lang=lang, label=html.escape(label), nav=nav, routing=html.escape(routing),
                             commit=commit, synced=html.escape(synced), embed=embed))
print("wrote", ", ".join(s + ".html" for s, *_ in pages), "+ assets/ to", out)
