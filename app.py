"""Novel search backend.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5050 in your browser.

Sites are loaded from sites.json (same folder as this file). Edit that file
by hand to add/remove/configure sites, or use the Add Site form in the UI.
"""
from flask import Flask, request, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import os

app = Flask(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
SITES_FILE = os.path.join(HERE, "sites.json")

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def load_sites():
    if not os.path.exists(SITES_FILE):
        return []
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sites(sites):
    with open(SITES_FILE, "w", encoding="utf-8") as f:
        json.dump(sites, f, indent=2, ensure_ascii=False)
        f.write("\n")


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


@app.route("/sites", methods=["GET"])
def list_sites():
    sites = load_sites()
    return jsonify([
        {"name": s.get("name"), "url": s.get("url"), "search_url": s.get("search_url")}
        for s in sites
    ])


@app.route("/sites", methods=["POST"])
def add_site():
    body = request.get_json(force=True) or {}
    missing = [k for k in ("name", "search_url") if not (body.get(k) or "").strip()]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    sites = load_sites()
    name = body["name"].strip()
    if any(s.get("name") == name for s in sites):
        return jsonify({"error": f"A site named '{name}' already exists."}), 400

    new_site = {
        "name": name,
        "url": (body.get("url") or "").strip() or body["search_url"].strip(),
        "search_url": body["search_url"].strip(),
        "method": (body.get("method") or "GET").upper(),
        "param": (body.get("param") or "q").strip(),
        "result_selector": (body.get("result_selector") or "ul.txt-list li span.s2 a").strip(),
        "title_selector": (body.get("title_selector") or "").strip() or None,
        "not_found_text": (body.get("not_found_text") or "").strip() or None,
    }
    sites.append(new_site)
    save_sites(sites)
    return jsonify({"ok": True, "site": new_site})


@app.route("/sites/<name>", methods=["DELETE"])
def remove_site(name):
    sites = load_sites()
    new_sites = [s for s in sites if s.get("name") != name]
    if len(new_sites) == len(sites):
        return jsonify({"error": "Site not found"}), 404
    save_sites(new_sites)
    return jsonify({"ok": True})


@app.route("/search", methods=["POST"])
def search():
    payload = request.get_json(force=True) or {}
    novel = (payload.get("novel") or "").strip()
    if not novel:
        return jsonify({"error": "Novel name required"}), 400

    sites = load_sites()
    results = []
    for site in sites:
        site_name = site.get("name") or site.get("url") or "?"
        try:
            res = search_site(site, novel)
            if res.get("found"):
                results.append({
                    "site": site_name,
                    "status": "found",
                    "result_url": res["url"],
                    "title": res.get("title"),
                })
            else:
                results.append({
                    "site": site_name,
                    "status": "not_found",
                    "message": f'Nothing found for "{novel}" on {site_name}.',
                })
        except Exception as e:
            results.append({
                "site": site_name,
                "status": "error",
                "message": f"Error fetching {site_name}: {e}",
            })
    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
