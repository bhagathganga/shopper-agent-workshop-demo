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
  pre {{ background: #fff; border: 1px solid #ddd; padding: 12px; overflow: auto; font-size: 12px; }}
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
  <h3>data-routing-attributes</h3>
  <pre>{routing}</pre>
  <p><small>App commit {commit} · assets synced from {synced}</small></p>
</main>
<script>
  document.getElementById('new-chat').onclick = function () {{
    [sessionStorage, localStorage].forEach(function (s) {{
      Object.keys(s).forEach(function (k) {{ if (/cim|miaw|scrt|convers|messag|cc_/i.test(k)) s.removeItem(k); }});
    }});
    location.reload();
  }};
</script>
<!-- ===== app embed output (target: body) ===== -->
{embed}
</body>
</html>
"""

os.makedirs(out, exist_ok=True)
shutil.copytree(os.path.join(EXT, "assets"), os.path.join(out, "assets"), dirs_exist_ok=True)
for slug, label, over, settings_over in pages:
    ctx = dict(base, **over, block={"settings": dict(defaults, **settings_over)})
    embed = tpl.render(**ctx).strip()
    routing = re.search(r'data-routing-attributes="([^"]*)"', embed).group(1)
    routing = json.dumps(json.loads(html.unescape(routing)), indent=2)
    nav = "".join('<a href="%s.html"%s>%s</a>' % (s, ' class="on"' if s == slug else "", l)
                  for s, l, _, _ in pages)
    lang = "fr" if slug == "fr-ca" else "en"
    with open(os.path.join(out, slug + ".html"), "w") as f:
        f.write(SHELL.format(lang=lang, label=html.escape(label), nav=nav, routing=html.escape(routing),
                             commit=commit, synced=html.escape(synced), embed=embed))
print("wrote", ", ".join(s + ".html" for s, *_ in pages), "+ assets/ to", out)
