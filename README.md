# Shopper Agent Workshop Demo

A tiny, single-file web page that mounts the **Salesforce Commerce Shopper Agent** chat
widget so you can test an agent built with **Shopper Agent Setup** — no storefront, no
build step, no deploy. Paste the Embedded Service Deployment (ESD) connection snippet and
chat.

The whole app is one file: [`index.html`](./index.html) (HTML + inline CSS + inline JS).

---

## Quick start

**Option A — hosted page.** Open the deployed URL (see [Deploying](#deploying)) and go.

**Option B — run locally** (recommended for a dry run — fastest way to see edits):

```bash
cd shopper-agent-workshop-demo
python3 -m http.server 8000
# open http://localhost:8000
```

Opening `index.html` directly (`file://…`) mostly works too, but a local server avoids
browser restrictions on the CDN script / storage.

---

## Configure

1. In your org, run **Shopper Agent Setup**, then open the Embedded Service Deployment and
   click **Install Code Snippet**. Copy the JSON, e.g.:
   ```json
   {
     "channelAddressIdentifier": "…",
     "OrganizationId": "00D…",
     "DeveloperName": "My_Shopper_Agent_CC_ES",
     "Url": "https://….my.salesforce-scrt.com"
   }
   ```
2. Paste it into the box on the page and click **Connect**.

Only `Url`, `OrganizationId`, and `DeveloperName` are used; `channelAddressIdentifier` is
ignored and the capabilities version is fixed at **65**. Config is stored only in your
browser (`localStorage`); **Clear saved config** wipes it.

---

## Live overrides (URL params) — no redeploy

For live troubleshooting you can tweak behavior with URL parameters, as either a query
string (`?key=val`) or a hash (`#key=val`). The **hash is preferred** — it never reaches a
server or log and works cleanly on static hosts; when a key appears in both, the hash wins.
**The bare base URL uses all defaults and behaves normally** — params are purely additive.

| Param | Effect | Default |
|---|---|---|
| `cdn=1.37.0` | Widget CDN version | `1.37.0` |
| `bundle=<full-url>` | Full `messaging.umd.js` URL (overrides `cdn`) | — |
| `dev=1` | Developer mode: `isDevelopment` + logs widget lifecycle events | off |
| `debug=1` | On-screen debug panel: effective config + load/inject errors (click to hide) | off |
| `capv=65` | `capabilitiesVersion` | `65` |
| `cartmgmt=0\|1` | Send `isCartMgmtSupported` (product tiles as in-chat buttons). Opt-in — omitted unless set | omitted |
| `autoscroll=0\|1` | Follow new agent messages (`0` stops the view following responses) | widget default (on) |
| `newtab=0\|1` | Open inline links in a new tab | `1` |
| `escalation=0\|1` | `enableEscalationToAgent` | `0` |
| `primary=%230176d3` | Theme primary color (URL-encode the leading `#`) | `#0176d3` |
| `header=Text` | Chat header label | `Shopper Agent` |
| `scrt2=` `org=` `es=` | Prefill / deep-link a connection (also accepts `Url`/`OrganizationId`/`DeveloperName`) | — |
| `connect=1` | Auto-connect when a full connection is available | — |
| `reset=1` | Clear saved config on load | — |
| `help=1` | List the params on the config screen | — |

Examples:
```
…/#debug=1                      show the debug panel
…/#dev=1                        developer mode + event stream
…/#cdn=1.34.1                   pin the team-bug-bashed build (fallback)
…/#cartmgmt=1                   opt into in-chat product cards (needs channel support)
…/#scrt2=https://x.my.salesforce-scrt.com&org=00D…&es=My_ES&connect=1   deep-link
…/#reset=1                      wipe saved config
```

> **On stage:** if the widget won't load, open `…/#debug=1` — the panel shows the exact
> bundle URL, the effective config, and any load/inject error, so you can tell instantly
> whether it's the CDN, the config, or the widget.

---

## Product links & mobile

- **Product cards** navigate to the storefront PDP by default. To make them behave like
  in-chat reply pills, opt in with `#cartmgmt=1` — this sends `isCartMgmtSupported` as a
  routing attribute, which the channel must declare (Commerce Quick Setup channels created
  after Apr 2026 do; older/external channels don't, and sending it there causes a 400).
  It's opt-in precisely so the demo connects against any org out of the box.
- **Mobile works** — the widget ships responsive CSS + a full-height panel, and this page
  has its own `≤640px` layout. Pre-connect on the phone (config persists), then screen-mirror.

---

## Deploying

GitHub Pages for this repo is served from the **`main` branch, root path (`/`)** — so the
page is just `index.html` at the repo root. Any push to `main` rebuilds the site in ~1 min.

**If you have push access to the upstream repo:**
```bash
git add index.html docs/
git commit -m "Workshop demo: paste-first flow, pinned CDN, in-chat cards, URL overrides"
git push origin main
# wait ~1 min → https://<owner>.github.io/shopper-agent-workshop-demo/
```

**If you do NOT have push access** (the common case if you cloned someone else's repo) —
fork it to your own account so you control the workshop copy:
```bash
gh repo fork bhagathganga/shopper-agent-workshop-demo --clone=false --remote=true
git push fork main                       # pushes your changes to your fork
gh api -X POST repos/<you>/shopper-agent-workshop-demo/pages \
  -f 'source[branch]=main' -f 'source[path]=/'   # enable Pages once
# → https://<you>.github.io/shopper-agent-workshop-demo/
```
(You can also enable Pages in the fork's **Settings → Pages → Source: main / root**.)

**Fastest of all for a dry run:** don't deploy — just run locally (see Quick start) and
edit `index.html`; refresh to see changes immediately.

---

## Repo layout

```
index.html                     the entire demo app
docs/workshop/README.md         facilitator notes + change log for this page
docs/superpowers/specs/…        original design spec
```

Facilitator prep docs (stage script, architecture, FAQ, PWA Kit/localhost) are kept
**outside this public repo** at `/Users/scanchi/Private/` — see `docs/workshop/README.md`.
