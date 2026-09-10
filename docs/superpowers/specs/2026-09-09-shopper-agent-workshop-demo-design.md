# Shopper Agent Workshop Demo — Design

**Date:** 2026-09-09
**Status:** Approved (design), pending implementation plan

## Purpose

A standalone React web app that connects to a Salesforce Shopper Agent over the
Messaging for In-App & Web (MIAW) **scrt2** endpoint. Built for a Dreamforce
workshop: it is hosted externally (GitHub Pages, eventually) so each attendee can
open it in a browser and talk to *their own* core org's shopper agent by entering
their own connection config. No SFCC storefront, no server, no cart.

Success = an attendee pastes their MIAW config, and gets a working, streaming,
multi-format chat with their agent (text, markdown, product carousels,
comparison pills / quick replies, typing indicators).

## Key decisions

- **Reuse the pre-built Cimulate widget, do not build the protocol.** The
  `@cimulate/copilot-widget` UMD bundle (`messaging.umd.js`) already implements the
  full scrt2 MIAW guest-token flow, SSE streaming, and multi-format rendering
  (markdown, carousels, quick-reply pills, typing indicators, conversation history).
  We embed it rather than reimplementing SSE parsing. Reference:
  `SalesforceCommerceCloud/plugin_commerce_client` embeds this same bundle via
  `window.CimulateMessaging.injectMessagingWidget(config)`.
- **Scope: conversational + product discovery only.** Search, carousels,
  recommendations, comparison pills, Q&A. **No cart management** — that requires
  per-request SFRA session tokens (`SfraAuthToken`, `RefreshToken`, `UsId`) which a
  standalone app has no way to produce. Explicitly out of scope.
- **Guest (unauthenticated) session.** The widget mints an anonymous MIAW token
  at runtime; no secrets in the client.
- **Per-attendee config.** Each workshop user supplies their own org's scrt2
  values through an in-app config screen. Nothing is hardcoded to one org.
- **Hosting is irrelevant to runtime.** GitHub Pages serves the static bundle once;
  all live traffic (token, SSE, messages) goes browser → scrt2 directly. Works
  identically on localhost and GitHub Pages.

## Stack

- Vite + React + TypeScript
- The Cimulate messaging bundle loaded from CDN:
  `https://cdn.search.cimulate.ai/copilot-widget/1.24.7/messaging.umd.js`
- No SSE / markdown / carousel libraries needed in our code — the bundle owns all of it.

## Architecture

```
src/
  config.ts            // ConfigValues type; localStorage load/save/clear; NTO example defaults
  ConfigForm.tsx       // paste-JSON box (auto-fills fields) + individual fields; validates
  useCimulateWidget.ts // loads messaging.umd.js, waits for window.CimulateMessaging,
                        //   calls injectMessagingWidget once; exposes load status/error
  App.tsx              // config gate -> branded page shell + widget mount point
  theme.ts             // brand colors passed to the widget's `theme`
index.html             // <div id="chat"> mount target
```

### Config values (per attendee)

| Field | Source in the pasted JSON | Default |
|---|---|---|
| `scrt2Url` | `Url` | — (required) |
| `orgId` | `OrganizationId` | — (required) |
| `esDeveloperName` | `DeveloperName` | — (required) |
| `capabilitiesVersion` | — | `"65"` |
| `headerText` (brand label) | — | `"Shopper Agent"` |

The pasted JSON uses the MIAW field names (`Url`, `OrganizationId`,
`DeveloperName`, `channelAddressIdentifier`). The paste box maps those to the
form fields. `channelAddressIdentifier` is captured but not required by
`injectMessagingWidget` — retained in case it is needed.

Example (Northern Trail Outfitters — shown prefilled as a sample):

```json
{
  "channelAddressIdentifier": "866ca16e-f5c9-49f5-b2b5-250c5f4a34ee",
  "OrganizationId": "00DWt00000KCYnB",
  "DeveloperName": "NTO_Shopper_Agent_ES_Custom",
  "Url": "https://storm-b76c200d4b76c7.my.salesforce-scrt.com"
}
```

## Data flow

1. **First load / no saved config** → `App` shows `ConfigForm`. Attendee pastes
   their JSON (auto-fills fields) or types fields directly, then submits.
2. Config is validated (required fields present, `scrt2Url` looks like a URL) and
   saved to `localStorage`.
3. `useCimulateWidget` injects the CDN `<script>`, waits for
   `window.CimulateMessaging.injectMessagingWidget`, and calls it **once** with:

   ```js
   injectMessagingWidget({
     elementId: "chat",
     mode: "messaging",
     componentConfig: {
       isOpen: true,
       isMinimized: false,
       options: { dialogFullHeight: true }   // FAB hidden — the panel is the centerpiece
     },
     messagingConfig: {
       scrt2Url, orgId, esDeveloperName,
       capabilitiesVersion,
       enableEscalationToAgent: false
     },
     theme,                 // NTO/brand colors
     headerText             // brand label
   })
   ```

4. The widget handles everything after that: token, conversation create, SSE
   stream, streaming replies, carousels, pills, typing indicators.
5. **⚙️ Settings** button lets the attendee edit/reset config. Because the bundle
   initializes once per page load, applying a new config tears down and re-mounts
   (or reloads the page) so the widget re-initializes against the new org.

## Look & feel

Clean, centered chat panel on a light brand-colored page. Achieved by opening the
widget inline (`isOpen:true`, `dialogFullHeight:true`), hiding the FAB, and
centering the `#chat` mount. Brand colors via the widget `theme`. Deeper visual
customization is possible via the bundle's `overridesUrl` component-override hook,
but we start theme-only and only reach for overrides if needed.

## Error handling

- **CDN script fails to load** (blocked host / booth WiFi): `useCimulateWidget`
  surfaces a visible "Couldn't load the assistant — retry" state, not a blank card.
- **Invalid config**: `ConfigForm` blocks submit and shows which field is wrong;
  bad JSON paste shows a parse error without clearing the form.
- **Connection / SSE errors**: handled inside the widget bundle.

## Deployment

- Local-first: `npm run dev`.
- Production: `vite build` → static `dist/`. For GitHub Pages, set Vite `base` to
  the repo name and deploy via a `gh-pages` branch or GitHub Actions. Documented
  here but not built in the first pass (local-first was chosen).

## Testing

- Unit: `config.ts` — JSON-paste mapping (MIAW field names → form fields),
  validation, localStorage round-trip.
- Smoke: `useCimulateWidget` injects the script and calls `injectMessagingWidget`
  with the correct config shape (mocked `window.CimulateMessaging`).
- The widget internals are third-party and are not tested here.

## Contingency

If `cdn.search.cimulate.ai` is unreachable from the attendee environment, plan B
is self-hosting the `messaging.umd.js` (+ CSS) bundle inside the app (the
reference cartridge supports this "static" mode). Noted as a fallback, not built
initially.

## Out of scope

- Cart management / any authenticated shopper session.
- Building the MIAW SSE/protocol layer by hand.
- SFCC/SFRA storefront integration.
