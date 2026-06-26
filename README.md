# OSINT Indonesia v4

OSINT Indonesia v4 adalah tools berbasis Python untuk melakukan pencarian informasi dari **sumber OSINT (Open Source Intelligence) publik** menggunakan data seperti **NIK** dan **Nomor Handphone Indonesia**.

> **Disclaimer:** Tools ini **tidak mengambil data dari database ilegal, hasil kebocoran data (data breach), ataupun database privat**. Seluruh hasil berasal dari sumber informasi publik yang tersedia di internet.

---

## Features

* 🔍 Pencarian berdasarkan NIK Indonesia
* 📱 Pencarian berdasarkan Nomor Handphone Indonesia
* ⚡ Multi-threaded Google Dork Scanner
* 🗺️ Decode kode wilayah Indonesia (Provinsi, Kabupaten/Kota, Kecamatan)
* 📄 Generate laporan HTML otomatis
* 🐍 Dibuat menggunakan Python 3

---

## Files

```
osint-indonesia-v4/
│
├── osint_v4.py          # Main scanner
├── kode_wilayah.json    # Database kode wilayah Indonesia
└── README.md
```

---

## Installation

Install Python dan pip:

```bash
sudo apt update
sudo apt install python3 python3-pip -y
```

Clone repository:

```bash
git clone https://github.com/spyschools/osint-indonesia-v4.git
cd osint-indonesia-v4
chmod +x *
```

Install dependency:

```bash
pip3 install requests beautifulsoup4
```

---

## Usage

Scan menggunakan NIK:

```bash
python3 osint_v4.py 3208074509870004
```

Scan menggunakan NIK dan Nomor HP:

```bash
python3 osint_v4.py 3275124308050003 +6281234567890
```

---

## Output

Setelah proses selesai akan dihasilkan file laporan:

```
report_TIMESTAMP.html
```

Buka file tersebut menggunakan browser.

---

## Notes

* Google dapat menerapkan **rate limit** terhadap scraping. Gunakan tools ini secara wajar.
* Jika API **wilayah.id** berubah atau tidak tersedia, proses generator `kode_wilayah.json` dapat gagal. Anda dapat mengisi file tersebut secara manual.
* Hasil pencarian bergantung pada informasi yang tersedia secara publik di internet.
* Akurasi hasil tidak dijamin 100%.

---

## Disclaimer

Project ini dibuat **hanya untuk tujuan edukasi, penelitian keamanan (security research), pengujian, dan pengembangan perangkat lunak**.

Pengguna bertanggung jawab penuh atas penggunaan tools ini. Penulis tidak bertanggung jawab atas penyalahgunaan, pelanggaran hukum, maupun aktivitas yang melanggar privasi pihak lain.

Gunakan tools ini dengan **bijak, bertanggung jawab, dan sesuai dengan hukum yang berlaku**.

---

## License

MIT License

---

## Author

**Spy Schools**

GitHub: https://github.com/spyschools
