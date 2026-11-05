"""Build docs/index.html, the project documentation page, from the working tree.

usage: python3 -I scripts/build-docs.py        (or: npm run docs)
The embed settings table is generated from the block's {% schema %}, so rerun after changing the block.
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "index.html")
EXT = "extensions/shopper-agent-widget"
# Served by GitHub Pages at /canadagoose/shopify-app/docs/, so the preview pages are a relative hop away.
SRC_URL = "https://github.com/bhagathganga/shopper-agent-workshop-demo/blob/main/canadagoose/shopify-app"
PREVIEW = "../../shopify/"

files = ["shopify.app.toml", "package.json", f"{EXT}/shopify.extension.toml", f"{EXT}/blocks/shopper_agent.liquid",
         f"{EXT}/assets/cimulate-init.js", f"{EXT}/assets/commerceClient.css", f"{EXT}/assets/cg-contact-menu.js",
         f"{EXT}/assets/cg-contact-menu.css", f"{EXT}/assets/commerce-client-icon.svg",
         f"{EXT}/locales/en.default.json", f"{EXT}/locales/fr.json",
         "scripts/sync-from-cartridge.sh", "scripts/render-preview.py", "scripts/build-docs.py"]
src = {f: open(os.path.join(ROOT, f)).read() for f in files}
liquid = src[f"{EXT}/blocks/shopper_agent.liquid"]
schema = json.loads(re.search(r"{% schema %}(.*?){% endschema %}", liquid, re.S).group(1))
synced = re.search(r"assets synced from: (.*?) {%", liquid).group(1)
e = html.escape


def settings_rows():
    rows = []
    for s in schema["settings"]:
        if s["type"] == "header":
            rows.append(f'<tr class="grp"><td colspan="4">{e(s["content"])}</td></tr>')
            continue
        default = s.get("default", "")
        if isinstance(default, bool):
            default = "on" if default else "off"
        if s["type"] == "select":
            opts = ", ".join(f'<code>{e(o["value"])}</code>' for o in s["options"])
            kind = f"select: {opts}"
        else:
            kind = e(s["type"])
        info = f'<br><small>{e(s["info"])}</small>' if s.get("info") else ""
        rows.append(f'<tr><td><code>{e(s["id"])}</code></td><td>{e(s["label"])}{info}</td>'
                    f'<td>{kind}</td><td>{f"<code>{e(str(default))}</code>" if default != "" else "<small>(blank)</small>"}</td></tr>')
    return "\n".join(rows)


def file_rows():
    return "\n".join(f'<tr><td><a href="{SRC_URL}/{e(f)}"><code>{e(f)}</code></a></td>'
                     f'<td>{len(src[f].encode()):,} B</td></tr>' for f in files)


page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Canada Goose Shopper Agent · Shopify theme app extension</title>
<style>
  :root {{ --ink:#181818; --muted:#666; --rule:#e2e2df; --bg:#f6f6f4; --code:#f0f0ec; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font:15px/1.6 Arial, sans-serif; color:var(--ink); background:var(--bg); }}
  header {{ background:#000; color:#fff; padding:18px 32px; }}
  header b {{ letter-spacing:.2em; }}
  header span {{ color:#aaa; margin-left:12px; font-size:13px; }}
  .wrap {{ display:flex; max-width:1180px; margin:0 auto; }}
  nav {{ position:sticky; top:0; align-self:flex-start; width:220px; padding:32px 16px 32px 32px; font-size:14px; }}
  nav a {{ display:block; color:var(--ink); text-decoration:none; padding:3px 0; }}
  nav a:hover {{ text-decoration:underline; }}
  main {{ flex:1; min-width:0; padding:24px 32px 64px; }}
  section {{ background:#fff; border:1px solid var(--rule); padding:8px 28px 20px; margin-bottom:20px; }}
  h1 {{ font-size:26px; margin:16px 0 4px; }}
  h2 {{ font-size:19px; border-bottom:1px solid var(--rule); padding-bottom:8px; }}
  .lede {{ color:var(--muted); margin-top:0; }}
  code {{ font:12.5px Menlo, Consolas, monospace; background:var(--code); padding:1px 4px; }}
  pre {{ background:var(--code); padding:14px; overflow:auto; max-height:520px; margin:0; }}
  pre code {{ background:none; padding:0; }}
  table {{ border-collapse:collapse; width:100%; font-size:14px; }}
  th, td {{ overflow-wrap:anywhere; text-align:left; vertical-align:top; padding:7px 10px; border-bottom:1px solid var(--rule); }}
  th {{ background:var(--bg); }}
  tr.grp td {{ background:#000; color:#fff; font-weight:700; font-size:13px; }}
  small {{ color:var(--muted); }}
  .callout {{ border-left:4px solid #000; background:var(--bg); padding:10px 14px; margin:14px 0; }}
  .callout.warn {{ border-color:#b00020; }}
  .pills a {{ display:inline-block; margin:0 8px 8px 0; padding:6px 12px; border:1px solid var(--ink);
             color:var(--ink); text-decoration:none; font-size:14px; }}
  .pills a:hover {{ background:var(--ink); color:#fff; }}
  ol li, ul li {{ margin:4px 0; }}
  @media (max-width: 860px) {{ nav {{ display:none; }} main {{ padding:16px; }} section {{ padding:4px 16px 16px; }} }}
</style>
</head>
<body>
<header><b>CANADA GOOSE</b><span>Shopper Agent · Shopify theme app extension</span></header>
<div class="wrap">
<nav>
  <a href="#overview">Overview</a>
  <a href="#preview">Live preview</a>
  <a href="#mapping">SFCC → Shopify</a>
  <a href="#prechat">Pre-chat fields</a>
  <a href="#settings">Embed settings</a>
  <a href="#deploy">Deploy</a>
  <a href="#cors">CORS</a>
  <a href="#gaps">Gaps / next steps</a>
  <a href="#collab">Working on this repo</a>
  <a href="#files">Files</a>
</nav>
<main>
<h1>Shopper Agent chat · Shopify app embed</h1>
<p class="lede">Agentforce shopper agent (Cimulate copilot widget over SCRT2, Embedded Service
<code>Canada_Goose_Shopper_Agent_CC_ES</code>) on an Online Store 2.0 theme. Assets: {e(synced)}.</p>

<section id="overview">
<h2>Overview</h2>
<p>This is an <b>extension-only Shopify app</b> with no app server; everything runs in the storefront. It ships one
theme app extension (<code>type = "theme"</code>) containing one app embed block, <code>shopper_agent.liquid</code>
(target <code>body</code>). The block renders the same <code>#cimulate-messaging-widget</code> data-* contract that
<code>cimulate-init.js</code> (copied from <code>plugin_commerce_client</code>) reads, so the widget code is unchanged
from SFCC.</p>
<pre><code>shopify.app.toml                       app config (client_id filled by `shopify app config link`)
package.json                           dev / deploy / check scripts
{EXT}/
  shopify.extension.toml               type = "theme"
  blocks/shopper_agent.liquid          app embed (target: body) + settings schema
  assets/cimulate-init.js              widget bootstrap (from plugin_commerce_client, one guard patched)
  assets/commerceClient.css            widget styles
  assets/commerce-client-icon.svg      default header logo
  assets/cg-contact-menu.js / .css     canadagoose.com-style "Customer support" launcher menu
  locales/en.default.json, fr.json     launcher menu strings</code></pre>
<p>The Cimulate bundle itself loads from the CDN:
<code>https://cdn.search.cimulate.ai/copilot-widget/&lt;version&gt;/messaging.umd.js</code>.</p>
</section>

<section id="preview">
<h2>Live preview</h2>
<p>Static pages rendering <code>shopper_agent.liquid</code> with mock Shopify objects, connected to the real
UAT agent. Each page has an editable pre-chat JSON box.</p>
<p class="pills">
  <a href="{PREVIEW}index.html">Guest · en_CA · CAD</a>
  <a href="{PREVIEW}fr-ca.html">Invité · fr_CA · CAD</a>
  <a href="{PREVIEW}us-customer.html">Signed-in customer · en_US · USD</a>
  <a href="{PREVIEW}pdp.html">Product page · en_CA</a>
</p>
<p><small>The PDP preview turns on <i>Send the current product</i> with the handle as identifier
(<code>data-pdp-product-id="expedition-parka"</code>). In the real embed that setting is off by default.</small></p>
</section>

<section id="mapping">
<h2>SFCC cartridge → Shopify app</h2>
<table>
<tr><th>SFCC (plugin_commerce_client)</th><th>This app</th></tr>
<tr><td><code>messagingWidgetBody.isml</code> data-* contract</td><td><code>blocks/shopper_agent.liquid</code> (same attributes)</td></tr>
<tr><td>BM <code>cc_config</code> site preferences</td><td>App embed settings in the Theme Editor</td></tr>
<tr><td><code>cimulate-init.js</code>, CSS, icon</td><td><code>assets/</code> (copied by <code>npm run sync</code>, one guard patched in)</td></tr>
<tr><td><code>CommerceClient-GetPrechatConfig</code> handshake</td><td>Skipped; pre-chat values rendered by Liquid into <code>data-routing-attributes</code></td></tr>
</table>
<div class="callout warn"><b>Org ID is truncated to 15 characters on purpose.</b> With the 18-character ID the SCRT
<code>/eventrouter/v1/sse</code> stream returns 400 "OrgId in the header and token must match" and the widget shows
"Something went wrong". The Liquid does <code>| slice: 0, 15</code>, so either length is safe to paste.</div>
</section>

<section id="prechat">
<h2>Pre-chat fields (<code>data-routing-attributes</code>)</h2>
<p>Sent when a conversation is created. They only apply to a <i>new</i> conversation.</p>
<table>
<tr><th>Field</th><th>Source</th></tr>
<tr><td><code>Language</code></td><td><code>request.locale</code>: <code>fr</code> stays <code>fr</code>, everything else becomes <code>en</code></td></tr>
<tr><td><code>CountryCode</code></td><td><code>localization.country</code> (default <code>CA</code>)</td></tr>
<tr><td><code>Locale</code></td><td><code>&lt;lang&gt;_&lt;country&gt;</code></td></tr>
<tr><td><code>Currency</code></td><td><code>cart.currency</code>, falling back to the country currency</td></tr>
<tr><td><code>Consent_Checkbox</code></td><td><code>customer.accepts_marketing</code> → <code>Yes</code>/<code>No</code> (<code>No</code> for guests)</td></tr>
<tr><td><code>FirstName</code>, <code>LastName</code>, <code>Email</code>, <code>Phone_Number</code></td><td>Signed-in customer only, when <i>Send signed-in customer's…</i> is on; blank values omitted</td></tr>
<tr><td><code>ClientVersion</code></td><td>Widget version setting</td></tr>
<tr><td><code>isCartMgmtSupported</code></td><td>Hard-coded <code>"false"</code>: the Shopify cart is not wired to the agent</td></tr>
</table>
<p>Example (guest, en_CA):</p>
<pre><code>{{"Language":"en","CountryCode":"CA","Locale":"en_CA","Currency":"CAD",
 "ClientVersion":"1.50.4","isCartMgmtSupported":"false","Consent_Checkbox":"No"}}</code></pre>
</section>

<section id="settings">
<h2>App embed settings (Theme Editor → App embeds → <i>{e(schema["name"])}</i>)</h2>
<p><small>Generated from the block's <code>{{% schema %}}</code> by <code>npm run docs</code>. Defaults point at the CG UAT org.</small></p>
<table>
<colgroup><col style="width:22%"><col style="width:30%"><col style="width:16%"><col></colgroup>
<tr><th>id</th><th>Label</th><th>Type</th><th>Default</th></tr>
{settings_rows()}
</table>
</section>

<section id="deploy">
<h2>Deploy</h2>
<h3>Test on a Partner dev store</h3>
<ol>
  <li>Create a development store in the Partner dashboard (Stores → Add store → Development store).</li>
  <li>In the app folder:
<pre><code>npm install -g @shopify/cli         # if not installed
shopify app config link             # create/link app "Canada Goose Shopper Agent"; fills client_id
shopify app dev                     # pick the dev store; serves the extension in dev-preview mode</code></pre></li>
  <li>Open the Theme Editor link the CLI prints → <b>App embeds</b> → toggle <b>{e(schema["name"])}</b> on → Save.
      No settings change is needed for UAT.</li>
  <li>Add the store origins to the UAT Embedded Service CORS allowlist (<a href="#cors">below</a>). If you skip this,
      the widget loads but the SCRT token call is blocked.</li>
</ol>
<h3>Ship to the Canada Goose store</h3>
<pre><code>npm run check                       # theme check (RemoteAsset warning for the Cimulate CDN is expected)
shopify app deploy                  # releases an app version that includes the extension</code></pre>
<p>In the Partner dashboard choose <b>Custom distribution</b> and enter the CG store domain (e.g.
<code>cg-uat.myshopify.com</code>) to get an install link. After install, enable the app embed in their theme.
For production, change the SCRT2 URL, org ID and ESD name in the embed settings; no code change is needed.</p>
</section>

<section id="cors">
<h2>CORS origins to allow on the Embedded Service</h2>
<ul>
  <li><code>https://&lt;dev-store&gt;.myshopify.com</code></li>
  <li><code>https://*.shopifypreview.com</code> (Theme Editor and preview links), or the specific preview hosts</li>
  <li>The Canada Goose dev/staging store domains (e.g. <code>https://cg-uat.myshopify.com</code>) and production domain.
      <code>https://www.canadagoose.com</code> and <code>https://canada-goose-prod.myshopify.com</code> are already allowed.</li>
</ul>
</section>

<section id="gaps">
<h2>Known gaps / next steps</h2>
<ul>
  <li><b>Cart:</b> add-to-cart from chat is off (<code>isCartMgmtSupported=false</code>). Wiring it means handling the
      widget's cart events in JS and calling Shopify's <code>/cart/add.js</code> (or Storefront API cart mutations),
      then flipping the pre-chat flag.</li>
  <li><b>Product context:</b> on product pages the embed can send the Shopify product ID, handle or selected variant
      SKU. The agent's product tools search the CG catalog via Cimulate, so confirm which identifier resolves before
      turning on <i>Send the current product</i>.</li>
  <li><b>Product links</b> from the agent currently point at canadagoose.com URLs, not the Shopify store's.</li>
  <li><b>Upstream sync:</b> <code>npm run sync</code> re-copies assets from <code>plugin_commerce_client</code> main
      and fails loudly if the prechat code it patches changes shape.</li>
</ul>
</section>

<section id="collab">
<h2>Working on this repo</h2>
<ul>
  <li><b>Where:</b> <code>canadagoose/shopify-app/</code> in
      <a href="https://github.com/bhagathganga/shopper-agent-workshop-demo">shopper-agent-workshop-demo</a>; run commands
      from that folder. This page is served from <code>docs/</code> by GitHub Pages; the preview pages are
      <code>canadagoose/shopify/</code> (rebuild with <code>scripts/render-preview.py ../shopify</code>).</li>
  <li><b>Branches:</b> <code>main</code> is what gets deployed. Work on a branch (e.g. <code>cart-management</code>)
      and open a PR. Keep commits small; say what changed in the storefront, not just the file.</li>
  <li><b>Never commit credentials.</b> Shopify client secrets, Admin/Storefront tokens and <code>.env</code> files stay
      out of git (<code>.env</code> and <code>.shopify/</code> are in <code>.gitignore</code>). <code>client_id</code> in
      <code>shopify.app.toml</code> is not a secret but is per-developer; link your own app with
      <code>shopify app config link</code>, and don't commit someone else's.</li>
  <li><b>Changed the block?</b> Run <code>npm run docs</code> so this page's settings table matches the schema, and
      <code>npm run check</code> for theme check.</li>
  <li><b>Changed upstream?</b> Don't hand-edit <code>assets/cimulate-init.js</code>, <code>commerceClient.css</code> or the
      icon. They are copied from <code>plugin_commerce_client</code> by <code>npm run sync</code> and get overwritten.
      Put Shopify-only behaviour in the Liquid block or a separate asset (as <code>cg-contact-menu.js</code> does).</li>
  <li><b>Previewing without a store:</b> <code>scripts/render-preview.py &lt;out-dir&gt;</code> renders the block with mock
      Shopify objects (needs <code>pip install 'python-liquid&lt;2'</code>). Those are the pages under
      <a href="#preview">Live preview</a>.</li>
</ul>
<table>
<tr><th>Command</th><th>What it does</th></tr>
<tr><td><code>npm run dev</code></td><td><code>shopify app dev</code>: serve the extension to a dev store in preview mode</td></tr>
<tr><td><code>npm run deploy</code></td><td><code>shopify app deploy</code>: release an app version with the extension</td></tr>
<tr><td><code>npm run check</code></td><td>Theme check for the extension (the RemoteAsset warning for the Cimulate CDN is expected)</td></tr>
<tr><td><code>npm run sync</code></td><td>Refresh widget assets and default version from <code>plugin_commerce_client</code> main</td></tr>
<tr><td><code>npm run docs</code></td><td>Rebuild <code>docs/index.html</code> (this page)</td></tr>
</table>
</section>

<section id="files">
<h2>Files</h2>
<table>
<tr><th>Path</th><th>Size</th></tr>
{file_rows()}
</table>
</section>
</main>
</div>
</body>
</html>
"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(page)
print(os.path.relpath(OUT, ROOT), len(page.encode()), "bytes,", len(files), "files,",
      sum(1 for s in schema["settings"] if s["type"] != "header"), "settings")
