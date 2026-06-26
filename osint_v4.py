#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
osint_v3.py
- Parse NIK & Phone
- Multi-threaded Google Dorking (scrape search results)
- Generate HTML report
Usage:
  python3 osint_v3.py 3275124308050003 +6281234567890
Dependencies:
  pip3 install requests beautifulsoup4
"""
import sys, re, json, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import html

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64)"
TIMEOUT = 12
MAX_THREADS = 8

# Sites to dork (tweakable)
DORK_SITES = [
    "site:go.id",
    "site:ac.id",
    "site:facebook.com",
    "site:instagram.com",
    "site:olx.co.id",
    "site:shopee.co.id",
    "site:tokopedia.com",
    ""  # global
]
GOOGLE_SEARCH = "https://www.google.com/search?q={query}&num=10"

# load wilayah if present
WILAYAH_FILE = "kode_wilayah.json"
try:
    with open(WILAYAH_FILE, "r", encoding="utf-8") as wf:
        WIL = json.load(wf)
except Exception:
    WIL = {}

PROVIDER_PREFIX = {
  "0811":"Telkomsel","0812":"Telkomsel","0813":"Telkomsel","0821":"Telkomsel",
  "0814":"Indosat","0815":"Indosat","0816":"Indosat","0855":"Indosat",
  "0817":"XL","0818":"XL","0819":"XL","0895":"Tri","0896":"Tri","0881":"Smartfren"
}

def is_nik(s): return re.fullmatch(r"\d{16}", s) is not None
def is_phone(s): return re.fullmatch(r"(\+62\d{8,13}|08\d{8,13})", s) is not None

def parse_nik(nik):
    res = {"nik": nik, "provinsi": "Tidak diketahui", "kabupaten": "Tidak diketahui", "kecamatan": "Tidak diketahui"}
    if len(nik) != 16:
        return res
    kode_prov = nik[:2]
    # Attempt to find by startswith in WIL (key may be '32' or longer). try multiple matches.
    if WIL:
        # Find prov key exactly or starting with kode_prov
        prov_key = None
        for k in WIL.keys():
            if k.startswith(kode_prov):
                prov_key = k; break
        if prov_key:
            res["provinsi"] = WIL.get(prov_key, {}).get("nama", "Tidak diketahui")
            # find matching kab where kab key startswith prov_key
            kab_key_found = None
            for kabk, kabv in WIL[prov_key].get("kabupaten", {}).items():
                # kabk might be full code; check if nik startswith kabk[:len(kabk)]
                if nik.startswith(kabk[:len(kabk)]):
                    kab_key_found = kabk
                    break
            if kab_key_found:
                res["kabupaten"] = WIL[prov_key]["kabupaten"][kab_key_found].get("nama","Tidak diketahui")
                # kecamatan: try exact match by kode substring
                for kec_k, kec_n in WIL[prov_key]["kabupaten"][kab_key_found].get("kecamatan", {}).items():
                    if nik.startswith(kec_k[:len(kec_k)]):
                        res["kecamatan"] = kec_n
                        break
    # date & gender
    try:
        dd = int(nik[6:8])
        mm = int(nik[8:10])
        yy = int(nik[10:12])
        gender = "Laki-laki"
        if dd > 40:
            dd -= 40; gender = "Perempuan"
        # heuristic for full year
        cur = datetime.datetime.now().year % 100
        year_full = 2000 + yy if yy <= cur else 1900 + yy
        res["tanggal_lahir"] = f"{dd:02d}-{mm:02d}-{year_full}"
        res["jenis_kelamin"] = gender
    except Exception:
        pass
    return res

def parse_phone(phone):
    norm = phone
    if norm.startswith("+62"):
        norm = "0" + norm[3:]
    prefix = norm[:4]
    provider = PROVIDER_PREFIX.get(prefix, "Tidak diketahui")
    return {"input": phone, "normalized": norm, "prefix": prefix, "provider": provider}

def google_search_raw(query):
    url = GOOGLE_SEARCH.format(query=requests.utils.requote_uri(query))
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        # parse /url?q= links
        for a in soup.select("a"):
            href = a.get("href","")
            if href.startswith("/url?q="):
                u = href.split("/url?q=")[1].split("&")[0]
                if u.startswith("http"):
                    links.append(u)
        # fallback: href containing http
        if not links:
            for a in soup.select("a"):
                href = a.get("href","")
                if href and "http" in href and "google" not in href:
                    links.append(href)
        # dedup preserve order
        seen = set(); uniq = []
        for u in links:
            if u not in seen:
                seen.add(u); uniq.append(u)
        return uniq[:25]
    except Exception:
        return []

def dork_target_multisite(target, sites=DORK_SITES, max_workers=6):
    queries = []
    for s in sites:
        q = f'{s} "{target}"' if s else f'"{target}"'
        queries.append(q)
    results = {}
    with ThreadPoolExecutor(max_workers=min(len(queries), max_workers)) as ex:
        futures = { ex.submit(google_search_raw, q): q for q in queries }
        for fut in as_completed(futures):
            q = futures[fut]
            try:
                res = fut.result()
            except Exception:
                res = []
            results[q] = res
    return results

def generate_html_report(entries, filename=None):
    parts = []
    for e in entries:
        parts.append(f"<h2>{html.escape(e.get('title','Target'))}</h2>")
        parts.append("<table border='1' cellpadding='6' style='border-collapse:collapse'>")
        for k,v in e.get("summary",{}).items():
            parts.append(f"<tr><th style='text-align:left'>{html.escape(str(k))}</th><td>{html.escape(str(v))}</td></tr>")
        parts.append("</table>")
        parts.append("<h3>Dorking</h3>")
        for q,urls in e.get("dork",{}).items():
            parts.append(f"<b>{html.escape(q)}</b><ul>")
            for u in urls[:30]:
                parts.append(f"<li><a href='{html.escape(u)}' target='_blank'>{html.escape(u)}</a></li>")
            parts.append("</ul>")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = "".join(parts)
    doc = f"<!doctype html><html><head><meta charset='utf-8'><title>OSINT v3 Report</title></head><body><h1>OSINT v3 Report</h1><p>Generated: {ts}</p>{body}</body></html>"
    if not filename:
        filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(doc)
    return filename

def process_target(t):
    if is_nik(t):
        parsed = parse_nik(t)
        dork = dork_target_multisite(t, max_workers=6)
        return {"title": f"NIK {t}", "summary": parsed, "dork": dork}
    elif is_phone(t):
        parsed = parse_phone(t)
        dork = dork_target_multisite(parsed["normalized"], max_workers=6)
        return {"title": f"Phone {t}", "summary": parsed, "dork": dork}
    else:
        dork = dork_target_multisite(t, max_workers=6)
        return {"title": f"Unknown {t}", "summary": {"note":"format not recognized"}, "dork": dork}

def main(argv):
    if len(argv) < 2:
        print("Usage: python3 osint_v3.py <NIK/Phone> [NIK/Phone ...]")
        return
    targets = argv[1:]
    entries = []
    with ThreadPoolExecutor(max_workers=min(len(targets), MAX_THREADS)) as ex:
        futures = { ex.submit(process_target, t): t for t in targets }
        for fut in as_completed(futures):
            res = fut.result()
            entries.append(res)
            print(f"[+] Done: {res.get('title')}")
    out = generate_html_report(entries)
    print(f"[+] Report saved: {out}")

if __name__ == "__main__":
    import sys
    main(sys.argv)
