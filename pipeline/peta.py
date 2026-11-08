import json
import math
import pathlib
import re
from collections import Counter

from teks import ancaman

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STOP = set("""yang dengan atau dan dalam pidana penjara paling lama tahun bulan denda banyak kategori setiap orang barang siapa
diancam dipidana karena untuk dari pada tersebut sebagaimana dimaksud ayat pasal huruf ini itu adalah oleh atas terhadap
juga dapat tidak bagi suatu sesuatu apabila jika maka telah akan lebih yang tersebut dalam secara melakukan dilakukan
satu dua tiga empat lima enam tujuh delapan sembilan sepuluh belas puluh ratus ribu rupiah hari minggu undang
ketentuan seseorang sama""".split())
GANTI = {"kepunyaan": "milik", "kejahatan": "tindak", "pelanggaran": "tindak", "perbuatan": "tindak", "seumur": "seumur",
         "sengaja": "sengaja", "kealpaannya": "kealpaan", "kelalaiannya": "kealpaan", "kelalaian": "kealpaan"}


def kata(paragraf_list):
    teks = " ".join(paragraf_list).lower()
    return [GANTI.get(w, w) for w in re.findall(r"[a-z]{3,}", teks) if w not in STOP]


def vektor(dokumen):
    df = Counter(w for d in dokumen for w in set(d))
    n = len(dokumen)
    hasil = []
    for d in dokumen:
        tf = Counter(d)
        v = {w: (1 + math.log(c)) * math.log(n / df[w]) for w, c in tf.items()}
        panjang = math.sqrt(sum(x * x for x in v.values())) or 1
        hasil.append({w: x / panjang for w, x in v.items()})
    return hasil


def kosinus(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(w, 0) for w, x in a.items())


EMAS = {"362": "476", "363": "477", "365": "479", "338": "458", "340": "459", "351": "466", "372": "486",
        "378": "492", "310": "433", "284": "411", "406": "521", "480": "591", "156a": "300", "1": "1"}


def selaras(skor, ambang):
    n, m = len(skor), len(skor[0]) if skor else 0
    terbaik = [[0.0] * (m + 1) for _ in range(n + 1)]
    pilih = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            opsi = [(terbaik[i - 1][j], "lewati_lama"), (terbaik[i][j - 1], "lewati_baru")]
            if skor[i - 1][j - 1] >= ambang:
                opsi.append((terbaik[i - 1][j - 1] + skor[i - 1][j - 1], "pasang"))
                opsi.append((terbaik[i - 1][j] + skor[i - 1][j - 1] * 0.9, "gabung"))
            terbaik[i][j], pilih[i][j] = max(opsi)
    hasil, i, j = {}, n, m
    while i > 0 and j > 0:
        langkah = pilih[i][j]
        if langkah in ("pasang", "gabung"):
            hasil[i - 1] = j - 1
            i, j = (i - 1, j - 1) if langkah == "pasang" else (i - 1, j)
        elif langkah == "lewati_lama":
            i -= 1
        else:
            j -= 1
    return hasil


if __name__ == "__main__":
    lama = json.loads((DATA / "kuhp-lama.json").read_text())
    baru = json.loads((DATA / "kuhp-baru.json").read_text())
    for p in lama + baru:
        p["ancaman"] = ancaman(p["teks"])
    asli = [p.get("teks_asli") or p["teks"] for p in baru]
    semua = vektor([kata(p["teks"] + [p["judul_bab"]]) for p in lama] + [kata(t + [p["judul_bab"]]) for p, t in zip(baru, asli)])
    v_lama, v_baru = semua[:len(lama)], semua[len(lama):]
    bab_lama, bab_baru = {}, {}
    for i, p in enumerate(lama):
        bab_lama.setdefault((p["buku"] == 1, p["buku"], p["bab"]), []).append(i)
    for j, q in enumerate(baru):
        bab_baru.setdefault((q["buku"] == 1, q["buku"], q["bab"]), []).append(j)
    def gabung(vs):
        hasil = {}
        for v in vs:
            for w, x in v.items():
                hasil[w] = hasil.get(w, 0) + x
        panjang = math.sqrt(sum(x * x for x in hasil.values())) or 1
        return {w: x / panjang for w, x in hasil.items()}
    pusat_baru = {k: gabung([v_baru[j] for j in js]) for k, js in bab_baru.items()}
    pilihan = {}
    for kl, il in bab_lama.items():
        pusat = gabung([v_lama[i] for i in il])
        calon = sorted(((kosinus(pusat, pv), kb) for kb, pv in pusat_baru.items() if kb[0] == kl[0]), reverse=True)[:2]
        js = sorted({j for _, kb in calon for j in bab_baru[kb]})
        skor = [[kosinus(v_lama[i], v_baru[j]) for j in js] for i in il]
        for a, b in selaras(skor, 0.15).items():
            pilihan[il[a]] = js[b]
    peta = []
    for i, p in enumerate(lama):
        skor = sorted(((kosinus(v_lama[i], v_baru[j]), baru[j]["nomor"]) for j in range(len(baru))
                       if (baru[j]["buku"] == 1) == (p["buku"] == 1)), reverse=True)[:3]
        kandidat = [{"nomor": n, "skor": round(s, 3)} for s, n in skor if s >= 0.15]
        utama = baru[pilihan[i]]["nomor"] if i in pilihan else (kandidat[0]["nomor"] if kandidat and kandidat[0]["skor"] >= 0.2 else None)
        if utama and all(k["nomor"] != utama for k in kandidat):
            kandidat.insert(0, {"nomor": utama, "skor": round(kosinus(v_lama[i], v_baru[pilihan[i]]), 3) if i in pilihan else 0})
        peta.append({"lama": [p["nomor"]], "baru": [utama] if utama else [], "jenis": "diubah" if utama else "dihapus",
                     "draft_baru": [utama] if utama else [], "draft_jenis": "diubah" if utama else "dihapus",
                     "skor": next((k["skor"] for k in kandidat if k["nomor"] == utama), 0), "kandidat": kandidat,
                     "diverifikasi": False, "catatan": ""})
    keputusan = json.loads((DATA / "verifikasi.json").read_text()) if (DATA / "verifikasi.json").exists() else {"lama": {}, "baru": {}}
    for e in peta:
        k = keputusan["lama"].get(e["lama"][0])
        if k:
            e.update(baru=k["baru"], jenis=k["jenis"], catatan=k.get("catatan", ""), diverifikasi=True)
    asal = {n for e in peta for n in e["baru"]}
    for q in baru:
        if q["nomor"] not in asal:
            k = keputusan["baru"].get(q["nomor"])
            peta.append({"lama": [], "baru": [q["nomor"]], "jenis": "baru", "skor": 0, "kandidat": [],
                         "diverifikasi": bool(k), "catatan": k.get("catatan", "") if k else ""})
    (DATA / "kuhp-lama.json").write_text(json.dumps(lama, ensure_ascii=False, indent=1))
    (DATA / "kuhp-baru.json").write_text(json.dumps(baru, ensure_ascii=False, indent=1))
    (DATA / "peta.json").write_text(json.dumps(peta, ensure_ascii=False, indent=1))
    jenis = Counter(e["jenis"] for e in peta)
    dari = {e["lama"][0]: e for e in peta if e["lama"]}
    benar = [n for n, b in EMAS.items() if dari.get(n) and dari[n]["baru"] == [b]]
    print(f"peta {len(peta)} baris: {dict(jenis)}; emas {len(benar)}/{len(EMAS)} benar")
    for n, b in EMAS.items():
        if n not in benar:
            print("   salah", n, "->", dari.get(n, {}).get("baru"), "seharusnya", b, "kandidat", [k["nomor"] for k in dari.get(n, {}).get("kandidat", [])])
