# Banding KUHP

Bandingkan pasal KUHP lama (Wetboek van Strafrecht, terjemahan BPHN) dengan KUHP baru (UU 1/2023 sebagaimana diubah UU 1/2026): satu halaman per pasal, teks berdampingan, padanan pasal dan perbandingan ancaman pidana.

## Struktur

| Folder | Isi |
| --- | --- |
| `sumber/` | PDF dan teks sumber yang diunduh (tidak diedit) |
| `pipeline/` | Script Python: urai teks, koreksi OCR, terapkan UU 1/2026, draft padanan, server verifikasi |
| `data/` | JSON hasil pipeline, dibaca situs |
| `web/` | Situs statis Astro |

## Pemakaian

Prasyarat: Node.js 22.12 atau lebih baru yang didukung Astro 6, npm, dan Python 3.10 atau lebih baru.
Data JSON sudah disertakan; pipeline tidak perlu dijalankan untuk mencoba situs.

Pasang dependensi dan bangun situs dengan tautan ke alat verifikasi:

```bash
git clone https://github.com/banding-kuhp/banding-kuhp.git
cd banding-kuhp/web
npm ci
PUBLIC_VERIFIKASI=http://127.0.0.1:4322 npm run build
npm run preview -- --host 127.0.0.1 --port 4321
```

Di terminal kedua, dari folder utama repositori:

```bash
python3 pipeline/verifikasi.py
```

Buka http://127.0.0.1:4321 untuk situs, lalu menu **Verifikasi** untuk alat di
http://127.0.0.1:4322. Tautan pada halaman pasal langsung memilih pasal terkait.
Setelah menyimpan keputusan, klik **Perbarui situs**, tunggu selesai, lalu refresh situs.
Alat verifikasi hanya untuk penggunaan lokal: tidak memiliki autentikasi dan jangan dibuka ke internet.

Untuk membangun ulang data sumber, jalankan `bash pipeline/jalankan.sh` dari folder utama,
lalu bangun ulang situs. Untuk situs publik, jalankan `npm run build` dari `web/` tanpa
`PUBLIC_VERIFIKASI` agar menu alat lokal tidak ditampilkan; hasil statis berada di `web/dist/`.

Keputusan verifikasi disimpan di `data/verifikasi.json` dan selalu menang atas draft otomatis, jadi `jalankan.sh` aman dijalankan ulang. Daftar yang masih perlu ditinjau ada di halaman `/tinjau`.

## Status data

- KUHP baru: 625 pasal (termasuk 599A sisipan UU 1/2026), 288 penjelasan; dicocokkan kata demi kata dengan Wikisource.
- KUHP lama: 588 pasal; 14 pasal belum ada teksnya (143, 371, 406–412, 486–488, 499, 535).
- Padanan: draft otomatis, setiap pasangan perlu diverifikasi.

Alat bantu riset, bukan nasihat hukum. Peraturan perundang-undangan bukan objek hak cipta (Pasal 42 UU 28/2014).

## Lisensi

Kode proyek menggunakan [MIT License](LICENSE). Atribusi pengembang: [stevenmarp](https://github.com/banding-kuhp/banding-kuhp).
Lisensi kode tidak mengubah status hukum teks peraturan, salinan dokumen, atau materi pihak ketiga.
Rujukan sumber tersedia pada halaman Tentang; materi dari Wikisource mengikuti ketentuan sumbernya.
