import * as cheerio from "cheerio";

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " +
  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

export async function onRequestPost({ request }) {
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResp({ error: "Invalid JSON body" }, 400);
  }

  const site = body.site;
  const novel = (body.novel || "").trim();
  if (!site || !site.search_url) {
    return jsonResp({ error: "site config with search_url required" }, 400);
  }
  if (!novel) {
    return jsonResp({ error: "novel required" }, 400);
  }

  try {
    const result = await searchSite(site, novel);
    return jsonResp(result);
  } catch (e) {
    return jsonResp({ found: false, error: String(e && e.message ? e.message : e) });
  }
}

async function searchSite(site, novel) {
  const method = (site.method || "GET").toUpperCase();
  const param = site.param || "q";
  const searchUrl = site.search_url;
  const headers = {
    "User-Agent": UA,
    Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
  };

  let resp;
  if (method === "POST") {
    const form = new URLSearchParams();
    form.append(param, novel);
    resp = await fetch(searchUrl, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
  } else {
    const u = new URL(searchUrl);
    u.searchParams.set(param, novel);
    resp = await fetch(u.toString(), { method: "GET", headers });
  }
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

  const html = await decodeBody(resp);

  if (site.not_found_text && html.includes(site.not_found_text)) {
    return { found: false };
  }

  const $ = cheerio.load(html);
  const selector = site.result_selector || "a";
  const first = $(selector).first();
  if (first.length === 0 || !first.attr("href")) {
    return { found: false };
  }

  const href = first.attr("href");
  const absUrl = new URL(href, searchUrl).toString();

  let title;
  const titleSel = site.title_selector;
  if (titleSel) {
    const titleEl = first.find(titleSel).first();
    title = (titleEl.length ? titleEl.text() : first.text()).trim();
  } else {
    title = first.text().trim();
  }

  return { found: true, url: absUrl, title };
}

async function decodeBody(resp) {
  const buf = await resp.arrayBuffer();
  const ct = resp.headers.get("content-type") || "";
  const m = /charset=([^;]+)/i.exec(ct);
  let enc = m ? m[1].trim().toLowerCase() : null;
  if (!enc) {
    const sniff = new TextDecoder("utf-8", { fatal: false }).decode(buf.slice(0, 2048));
    const metaMatch = /<meta[^>]+charset=["']?([^"'>\s]+)/i.exec(sniff);
    if (metaMatch) enc = metaMatch[1].toLowerCase();
  }
  enc = enc || "utf-8";
  if (enc === "gb2312" || enc === "gb_2312-80") enc = "gbk";
  try {
    return new TextDecoder(enc, { fatal: false }).decode(buf);
  } catch (e) {
    return new TextDecoder("utf-8", { fatal: false }).decode(buf);
  }
}

function jsonResp(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}
