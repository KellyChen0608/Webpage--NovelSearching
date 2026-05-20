"""Novel search backend (local dev server).

Run:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5050 in your browser.

This is the local equivalent of the Cloudflare Pages Function in
functions/api/search.js. Both expose POST /api/search with the same contract,
so the same index.html works in both environments. Sites are managed in the
browser via localStorage; this server is purely a CORS-bypass scraper.
"""
from flask import Flask, request, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

app = Flask(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def search_site(config, novel):
    method = (config.get("method") or "GET").upper()
    param = config.get("param") or "q"
    payload = {param: novel}
    headers = {"User-Agent": UA}
    search_url = config["search_url"]
    if method == "POST":
        r = requests.post(search_url, data=payload, headers=headers, timeout=15)
    else:
        r = requests.get(search_url, params=payload, headers=headers, timeout=15)
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding
    html = r.text

    not_found_text = config.get("not_found_text")
    if not_found_text and not_found_text in html:
        return {"found": False}

    soup = BeautifulSoup(html, "html.parser")
    selector = config.get("result_selector") or "a"
    first = soup.select_one(selector)
    if not first or not first.get("href"):
        return {"found": False}

    href = first["href"]
    abs_url = urljoin(search_url, href)

    title_sel = config.get("title_selector")
    if title_sel:
        title_el = first.select_one(title_sel)
        title = title_el.get_text(strip=True) if title_el else first.get_text(strip=True)
    else:
        title = first.get_text(strip=True)

    return {"found": True, "url": abs_url, "title": title}


@app.route("/")
def index():
    return send_from_directory(HERE, "index.html")


@app.route("/api/search", methods=["POST"])
def api_search():
    body = request.get_json(force=True) or {}
    site = body.get("site") or {}
    novel = (body.get("novel") or "").strip()
    if not site or not site.get("search_url"):
        return jsonify({"error": "site config with search_url required"}), 400
    if not novel:
        return jsonify({"error": "novel required"}), 400
    try:
        res = search_site(site, novel)
        if res.get("found"):
            return jsonify({"found": True, "url": res["url"], "title": res.get("title")})
        return jsonify({"found": False})
    except Exception as e:
        return jsonify({"found": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
