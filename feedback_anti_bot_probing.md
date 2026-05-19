---
name: feedback-anti-bot-probing
description: "Don't rapid-fire probe URLs on sites with anti-bot guards — the user's IP can get blacklisted."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c35615d3-a5fa-4e7d-a5b9-7911bfd062d1
---

Don't probe multiple URL paths in rapid succession against sites that show anti-bot protection (e.g., `_guard/auto.js` JS challenges, IP-based rate limiting).

**Why:** On 2026-05-19, while trying to find the search URL pattern for `9ggd.com` (which uses a `_guard/auto.js` system), I sent 6 probe requests in a single loop. The site blacklisted the IP, and since the user's browser shared that IP, the user got blocked too ("访问已被阻止 — 您的 IP 地址已被列入黑名单"). Lost trust and required apology.

**How to apply:** Before probing an unfamiliar site, do a single test request first. If the response indicates anti-bot protection (a `_guard/`, Cloudflare challenge, `cf-mitigated`, etc.), STOP and ask the user how to proceed — don't keep trying paths. Options to suggest: ask the user to do one search manually and share the URL, use a headless browser like Playwright (executes the JS guard naturally), or skip that site.
