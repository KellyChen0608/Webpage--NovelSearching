---
name: project-novel-search-app
description: Flask+HTML tool at ~/Desktop/Internship/Webpage
metadata: 
  node_type: memory
  originSessionId: c35615d3-a5fa-4e7d-a5b9-7911bfd062d1
---

Searching for searching Chinese novels across configured sites. Config-driven via sites.json.
metadata:
  type: project
---

User is building a small web app at `/Users/kellychen/Desktop/Internship/Webpage---Searching/` to search a novel name across multiple Chinese novel sites. Stack: Flask backend (`app.py`) + single HTML page (`index.html`) served on `http://localhost:5050`. **Sites are stored server-side in `sites.json`**, with full scraping config per site (search URL, method, param, CSS selectors, not-found marker). No localStorage.

**Why:** Personal tool. Started 2026-05-19. User reads Chinese-language novels and wants to check across multiple sources at once. User prefers simple/lightweight over robust — chose against Playwright. Wanted preloaded sites and to add new ones without me updating code, which is why the design switched from per-site handler functions to a generic config-driven scraper.

**How to apply:**
- Adding a new site = adding an entry to `sites.json` (or using the "Add a site" UI form). No code changes. Default `result_selector` is the 笔趣阁 template `ul.txt-list li span.s2 a`, which works for many Chinese novel sites.
- For sites that need custom CSS selectors (e.g., 52shuku.net uses `article.excerpt header a` + `h4` title selector), set them explicitly in sites.json.
- Currently configured sites: 52shuku.net (GET, q), linnuojiaju.com (POST, searchkey), 6qxs.com (POST, s).
- Many Chinese novel sites (918z.net, 9ggd.com) use a `_guard/auto.js` JS-based anti-bot system that blocks plain HTTP. Don't try to bypass without Playwright. See [[feedback-anti-bot-probing]].
- API: `GET /sites`, `POST /sites` (add), `DELETE /sites/<name>`, `POST /search` with `{novel}`.
- Search returns the FIRST result on each site's results page, even if it's not an exact match — sites sort their own way; user can click through to refine.
