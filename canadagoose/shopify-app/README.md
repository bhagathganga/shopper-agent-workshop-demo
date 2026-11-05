# Canada Goose Shopper Agent — Shopify app

Extension-only Shopify app that puts the Agentforce shopper agent (Cimulate copilot widget over SCRT2,
Embedded Service `Canada_Goose_Shopper_Agent_CC_ES`) on an Online Store 2.0 theme as an **app embed**.
There is no app server: everything runs in the storefront.

**Full documentation:** https://bhagathganga.github.io/shopper-agent-workshop-demo/canadagoose/shopify-app/docs/
(source: [`docs/index.html`](docs/index.html)) covers the overview, pre-chat fields, every embed setting, deploy,
CORS, gaps and how to work on the repo. Live preview of the embed (mock Shopify objects, real UAT agent):
https://bhagathganga.github.io/shopper-agent-workshop-demo/canadagoose/shopify/pdp.html

This folder lives in the `shopper-agent-workshop-demo` repo; run every command below from
`canadagoose/shopify-app/`.

It is a port of `plugin_commerce_client`'s SFCC integration:

| SFCC cartridge                              | This app                                                   |
|---------------------------------------------|------------------------------------------------------------|
| `messagingWidgetBody.isml` data-* contract  | `blocks/shopper_agent.liquid` (same attributes)            |
| BM `cc_config` site preferences             | App embed settings in the Theme Editor                     |
| `cimulate-init.js`, CSS, icon               | `assets/` (copied by `npm run sync`, one guard patched in) |
| `CommerceClient-GetPrechatConfig` handshake | Skipped; pre-chat values are rendered by Liquid into `data-routing-attributes` |

Pre-chat fields sent when a conversation is created:

| Field | Source |
|---|---|
| `Language` | `request.locale` (`fr` stays `fr`, everything else becomes `en`) |
| `CountryCode` | `localization.country` |
| `Locale` | `<lang>_<country>` |
| `Currency` | `cart.currency` |
| `Consent_Checkbox` | `customer.accepts_marketing` (`No` for guests) |
| `FirstName`, `LastName`, `Email`, `Phone_Number` | Signed-in customer only (setting *Send signed-in customer's…*) |
| `ClientVersion` | Widget version |
| `isCartMgmtSupported` | `"false"` (Shopify cart is not wired to the agent) |

The org ID is truncated to 15 characters on purpose. With the 18-character ID, the SCRT `/eventrouter/v1/sse`
stream returns 400 "OrgId in the header and token must match", and the widget shows "Something went wrong".

## Layout

```
shopify.app.toml                       app config (client_id filled by `shopify app config link`)
extensions/shopper-agent-widget/
  shopify.extension.toml               type = "theme"
  blocks/shopper_agent.liquid          app embed (target: body) + settings schema
  assets/                              cimulate-init.js, commerceClient.css, commerce-client-icon.svg
scripts/sync-from-cartridge.sh         refresh assets + default widget version from plugin_commerce_client main
scripts/render-preview.py              render the block to static preview pages with mock Shopify objects
scripts/build-docs.py                  rebuild docs/index.html (`npm run docs`)
docs/index.html                        project documentation page
```

## Working on this repo

- `main` is what gets deployed. Work on a branch (e.g. `cart-management`) and open a PR.
- Never commit credentials: Shopify client secrets, Admin/Storefront tokens and `.env` files stay out of git.
  `client_id` in `shopify.app.toml` is per-developer; link your own app with `shopify app config link` and
  don't commit someone else's.
- Don't hand-edit `assets/cimulate-init.js`, `commerceClient.css` or the icon; `npm run sync` overwrites them.
  Put Shopify-only behaviour in the Liquid block or a separate asset (like `cg-contact-menu.js`).
- After changing the block, run `npm run docs` (settings table is generated from the schema) and `npm run check`.

## Test on a Partner dev store

1. Create a development store in the Partner dashboard (Stores → Add store → Development store).
2. In this folder:
   ```sh
   shopify app config link   # create a new app "Canada Goose Shopper Agent"; fills client_id
   shopify app dev           # pick the dev store; serves the extension in dev-preview mode
   ```
3. Open the Theme Editor link the CLI prints. Go to **App embeds** and toggle **Shopper Agent chat** on, then Save.
   Defaults point at the UAT org (`canadagoose--uat`), so no settings change is needed.
4. Add the store origins to the UAT Embedded Service CORS allowlist (see below). If you skip this, the widget
   loads but the SCRT token call is blocked.

## CORS origins to allow in UAT

- `https://<dev-store>.myshopify.com`
- `https://*.shopifypreview.com` (Theme Editor and preview links), or the specific preview hosts
- Later: the Canada Goose dev/staging store domains and the production domain
  (`https://www.canadagoose.com` and `https://canada-goose-prod.myshopify.com` are already allowed)

## Ship to the Canada Goose store

```sh
shopify app deploy   # releases a new app version that includes the extension
```

Then, in the Partner dashboard, choose **Custom distribution** and enter the CG store domain to get an
install link. After install, enable the app embed in their theme. When moving to production, change the
SCRT2 URL, org ID and ESD name in the embed settings; no code change is needed.

## Updating from the cartridge

```sh
npm run sync    # git pull ~/src/plugin_commerce_client, recopy assets, bump the widget version default
npm run check   # theme check (the RemoteAsset warning for the Cimulate CDN bundle is expected)
```

The sync fails loudly if the upstream prechat code it patches changes shape.

## Known gaps / next steps

- **Product context:** on product pages the embed sends the Shopify product ID, handle or variant SKU
  (setting). The agent's product tools search the CG catalog via Cimulate, so confirm with Cimulate which
  identifier resolves before turning on *Send the current product*.
- **Cart:** add-to-cart from chat is off (`isCartMgmtSupported=false`). Wiring it means handling the
  widget's cart events in JS and calling Shopify's `/cart/add.js`.
- **Product links** from the agent currently point at canadagoose.com URLs, not the Shopify store's.
