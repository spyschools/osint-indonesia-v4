#!/usr/bin/env python3
import requests
import json
import time
import os
import zipfile

BASE_URL = "https://wilayah.id/api"
OUTPUT_JSON = "kode_wilayah.json"
ZIP_NAME = "osint_v3.zip"

# =========================
# STEP 1: Ambil Data Wilayah
# =========================
def get_data(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[!] Error ambil {endpoint}: {e}")
        return {}

def generate_wilayah():
    print("[*] Mengambil data provinsi...")
    provinsi = get_data("provinsi")

    wilayah = {}
    for prov in provinsi.get("data", []):
        prov_id = prov.get("kode")
        wilayah[prov_id] = {"nama": prov.get("nama"), "kabupaten": {}}

        print(f" [+] {prov.get('nama')} ({prov_id})")
        kabupaten = get_data("kabupaten", {"provinsi_id": prov_id})
        time.sleep(0.5)

        for kab in kabupaten.get("data", []):
            kab_id = kab.get("kode")
            wilayah[prov_id]["kabupaten"][kab_id] = {
                "nama": kab.get("nama"),
                "kecamatan": {}
            }

            kecamatan = get_data("kecamatan", {"kabupaten_id": kab.get("kode")})
            time.sleep(0.5)

            for kec in kecamatan.get("data", []):
                kec_id = kec.get("kode")
                wilayah[prov_id]["kabupaten"][kab_id]["kecamatan"][kec_id] = kec.get("nama")

    # Backup file lama jika ada
    if os.path.exists(OUTPUT_JSON):
        os.rename(OUTPUT_JSON, OUTPUT_JSON + ".bak")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(wilayah, f, indent=4, ensure_ascii=False)

    print(f"[✓] Data wilayah lengkap tersimpan di {OUTPUT_JSON}")

# =========================
# STEP 2: Buat osint_v3.py
# =========================
def create_files():
    osint_code = r"""#!/usr/bin/env python3
import requests, json, re, html, os
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

TIMEOUT = 12
USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64)"
SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q={query}",
    "Bing": "https://www.bing.com/search?q={query}",
    "DuckDuckGo": "https://duckduckgo.com/html/?q={query}"
}

PROVIDER_PREFIX = {
    "0811": "Telkomsel","0812": "Telkomsel","0813": "Telkomsel","0821": "Telkomsel","0822": "Telkomsel","0823": "Telkomsel","0852": "Telkomsel","0853": "Telkomsel",
    "0856": "Indosat","0857": "Indosat","0858": "Indosat","0814": "Indosat","0815": "Indosat","0816": "Indosat",
    "0817": "XL","0818": "XL","0819": "XL","0877": "XL","0878": "XL","0879": "XL",
    "0895": "Tri","0896": "Tri","0897": "Tri","0898": "Tri","0899": "Tri",
    "0881": "Smartfren","0882": "Smartfren","0883": "Smartfren","0884": "Smartfren","0885": "Smartfren","0886": "Smartfren","0887": "Smartfren","0888": "Smartfren","0889": "Smartfren"
}

# ======================
# PHONEINFOGA-LITE
# ======================
def phoneinfoga_scan(phone):
    norm = phone
    if norm.startswith("+62"):
        norm = "0" + norm[3:]
    elif norm.startswith("62"):
        norm = "0" + norm[2:]

    prefix = norm[:4]
    provider = PROVIDER_PREFIX.get(prefix, "Tidak diketahui")
    results = {"normalized": norm, "provider": provider, "searches": {}}

    for name, base in SEARCH_ENGINES.items():
        url = base.format(query=requests.utils.requote_uri(norm))
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                links = []
                for a in soup.select("a"):
                    href = a.get("href","")
                    if href.startswith("http") and not any(b in href for b in ["google","bing","duckduckgo"]):
                        links.append(href)
                results["searches"][name] = links[:10]
        except Exception as e:
            results["searches"][name] = [f"Error: {e}"]
    return results

# ======================
# Multi-thread Dorking
# ======================
def dork_target_multisite(query, max_workers=6):
    results = {}
    def fetch(name, base):
        url = base.format(query=requests.utils.requote_uri(query))
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                links = [a.get("href") for a in soup.select("a") if a.get("href","").startswith("http")]
                return (name, links[:10])
        except Exception as e:
            return (name, [f"Error: {e}"])
        return (name, [])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch, n, b) for n,b in SEARCH_ENGINES.items()]
        for f in futures:
            n, links = f.result()
            results[n] = links
    return results

# ======================
# Export ke HTML
# ======================
def export_html(title, result_dict):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{ts}.html"
    html_out = f"<html><head><meta charset='utf-8'><title>OSINT Report</title></head><body>"
    html_out += f"<h2>OSINT Report: {html.escape(title)}</h2>"
    for target, sections in result_dict.items():
        html_out += f"<h3>Target: {html.escape(target)}</h3>"
        for section, data in sections.items():
            html_out += f"<h4>{html.escape(section)}</h4><pre>{html.escape(json.dumps(data, indent=2, ensure_ascii=False))}</pre>"
    html_out += "</body></html>"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"[✓] Report tersimpan di {filename}")

# ======================
# Proses Target
# ======================
def process_target(t):
    hasil = {}
    if t.isdigit() and len(t) == 16:
        print(f"[+] Target NIK: {t}")
        hasil["Dorking NIK"] = dork_target_multisite(t)

    elif re.match(r"^(\+62|62|0)8[1-9][0-9]{7,11}$", t):
        print(f"[+] Target Nomor HP: {t}")
        pfga = phoneinfoga_scan(t)
        dork = dork_target_multisite(pfga["normalized"])
        hasil["PhoneInfoga-lite"] = pfga
        hasil["Google Dork"] = dork
    else:
        print(f"[!] Format tidak dikenal: {t}")
    return hasil

# ======================
# MAIN
# ======================
def main():
    print("[*] OSINT v3 siap jalan (NIK/HP → hasil + HTML)")
    mode = input("Mode: (1) Single input, (2) Load dari file .txt ? ")

    all_results = {}

    if mode == "1":
        while True:
            t = input("Masukkan target (NIK/No HP, 'q' untuk keluar): ")
            if t.lower() == "q":
                break
            hasil = process_target(t)
            if hasil:
                all_results[t] = hasil
                export_html(t, {t: hasil})

    elif mode == "2":
        filename = input("Masukkan nama file .txt: ")
        if not os.path.exists(filename):
            print("[!] File tidak ditemukan")
            return
        with open(filename, "r", encoding="utf-8") as f:
            targets = [line.strip() for line in f if line.strip()]
        print(f"[*] Memproses {len(targets)} target dari {filename} ...")
        for t in targets:
            hasil = process_target(t)
            if hasil:
                all_results[t] = hasil
        if all_results:
            export_html("Batch Scan", all_results)

    else:
        print("[!] Mode tidak dikenal")

if __name__ == "__main__":
    main()
"""
    with open("osint_v3.py", "w", encoding="utf-8") as f:
        f.write(osint_code)

    readme = """# OSINT v3

Toolkit OSINT untuk pencarian data berbasis NIK & No HP.

## Fitur
- Scan NIK
- Scan Nomor HP (PhoneInfoga-lite)
- Multi-thread Google Dorking
- Export hasil ke HTML
- Batch scan dari file .txt

## Cara pakai
```bash
python3 osint_v3.py
```"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    print("[✓] File osint_v3.py & README.md berhasil dibuat")

# =========================
# STEP 3: Kompres ke ZIP
# =========================
def compress_to_zip():
    with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in [OUTPUT_JSON, "osint_v3.py", "README.md"]:
            if os.path.exists(file):
                zipf.write(file)
    print(f"[✓] Semua file dikompres ke {ZIP_NAME}")

# =========================
# MAIN EXECUTION
# =========================
if __name__ == "__main__":
    generate_wilayah()
    create_files()
    compress_to_zip()
