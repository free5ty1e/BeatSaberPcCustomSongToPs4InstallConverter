---
name: beatsage-api-capture
description: "The live-captured beatsage.com API contract (M13) + the third-party-API capture methodology: read the SPA's client bundle for the backend host, routes, and field names — never guess, never scrape."
metadata:
  type: reference
---

# The Beat Sage API capture (M13.3, 2026-10-22)

Beatsage.com is a Nuxt SPA whose backend host, routes, and multipart field
names are all readable from its own client bundle. The capture process
( reusable for any JS SPA service):

1. `curl` the homepage → find the `/_nuxt/*.js` script hashes.
2. One small file is the **webpack runtime** — read its chunk map
   (`{2:"96f10bf…"}`) to find the lazy page chunk.
3. Grep the bundles for `https://` hosts (found the Google Cloud Run
   `SERVER_HOST`), `serverFetch("route")` call sites, and the `FormData`
   construction right before the POST (field names verbatim).
4. The Vuex store module (in the vendors chunk) holds the DEFAULTS:
   `difficulties:["Hard","Expert"], modes:["Standard","90Degree"], …`.

## The captured contract (pinned by `tests/test_webapp_beatsage.py`)

- Host: `https://beatsage-v2-prod-http-f5hqh6gvya-uc.a.run.app` (Cloud Run;
  no auth, no cookies, no captcha — plain multipart)
- `POST /beatsaber_custom_level_create` — multipart fields: `audio_file`
  (file), `audio_metadata_title`, `audio_metadata_artist`, `difficulties`
  (csv), `modes` (csv), `events` (csv), `environment`, `system_tag` →
  `{"id": …}`
- `GET /beatsaber_custom_level_heartbeat/<id>` → `{"status": PENDING |
  LOADING_AUDIO | CREATING_LEVEL | FORMATTING_LEVEL | DONE}`
- `GET /beatsaber_custom_level_download/<id>` → the map zip (PK)
- Their UI polls every **3s** and tolerates **3 consecutive failures**
  (`progressFailsMax: 3`) — we mirror their cadence + budget exactly
- v2 offers NO Easy difficulty (Normal/Hard/Expert/ExpertPlus only) — our
  pipeline's Easy auto-fill covers the gap
- Option surface: modes Standard/NoArrows/OneSaber/90Degree/360Degree;
  events Bombs/DotBlocks/Obstacles/Lights; 16 environments; system v1|v2

## Respect rules (the plan's §2, encoded in `adapters/beatsage.py`)

- ONE job at a time; their cadence; their failure budget — never a hammer
- Their branding explicit in the UI; using the service = accepting THEIR terms
- The user asserts rights to the audio (the generated map is not for
  redistribution)
- **CI NEVER contacts them**: all tests mocked; the single live-contract
  test is gated behind `BEATSAGE_LIVE=1` and uses a rights-clean
  SYNTHESIZED tone (`development/scripts/make_rights_clean_test_song.py`)
- Any client failure degrades to the guided flow (Tier 2) — the ladder
  means a service change can never dead-end the feature

## Cross-references

- [[game-data-extractor]] — the other recent third-party-adjacent flow
- [[absent-vs-failed-doctrine]] — the Tier-2 fallback is the same "never a
  dead end" posture
