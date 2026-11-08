import json
import pathlib
import re
import sys

from teks import paragraf

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUMBER = ROOT / "sumber" / "lama" / "kejari.txt"
KELUAR = ROOT / "data" / "kuhp-lama.json"
BUKU = {"Kesatu": 1, "Kedua": 2, "Ketiga": 3}
PASAL = re.compile(r"^Pasal (\d+[a-z]?)\s*$")
BAB = re.compile(r"^Bab ([IVXLC]+[A-Z]?) - (.+)$")
BUKU_RE = re.compile(r"^Buku (Kesatu|Kedua|Ketiga) - (.+)$")
DAFTAR_ISI_SAMPAI = "Bab I - Batas-Batas Berlakunya"


INLINE = re.compile(r"(?<=\S)\s+(?=(?:Pasal \d+[a-z]?\s|Bab [IVXLC]+ - [A-Z]))")


def angka(nomor):
    return int(re.match(r"\d+", nomor).group())


def buku_dari(nomor):
    n = angka(nomor)
    return 1 if n <= 103 else 2 if n <= 488 else 3


def pecah(baris):
    hasil = []
    for b in baris:
        b = b.strip()
        for bagian in INLINE.split(b):
            m = re.match(r"^(Pasal \d+[a-z]?)\s+(.+)$", bagian)
            hasil.extend([m.group(1), m.group(2)] if m else [bagian])
    return hasil


def urai(baris):
    hasil, bab, judul_bab, sekarang, terakhir, dilihat = [], "I", "", None, 0, set()
    mulai = next(i for i, b in enumerate(baris) if b.startswith(DAFTAR_ISI_SAMPAI))
    lewati = False
    for b in pecah(baris[mulai:]):
        if not b:
            continue
        if BUKU_RE.match(b) or b == "Daftar Isi":
            lewati = True
            continue
        m = BAB.match(b)
        if m:
            bab, judul_bab = m.group(1), m.group(2).strip()
            continue
        m = PASAL.match(b)
        if m:
            lewati = False
        if lewati:
            continue
        if m and m.group(1) not in dilihat and terakhir <= angka(m.group(1)) <= terakhir + 15:
            terakhir = angka(m.group(1))
            dilihat.add(m.group(1))
            sekarang = {"nomor": m.group(1), "buku": buku_dari(m.group(1)), "bab": bab, "judul_bab": judul_bab, "baris": []}
            hasil.append(sekarang)
            continue
        if sekarang:
            sekarang["baris"].append(b)
    for p in hasil:
        p["teks"] = paragraf(p.pop("baris"))
    return hasil


if __name__ == "__main__":
    pasal = urai(SUMBER.read_text(encoding="utf-8").splitlines())
    nomor = [p["nomor"] for p in pasal]
    ganda = sorted({n for n in nomor if nomor.count(n) > 1})
    KELUAR.parent.mkdir(exist_ok=True)
    KELUAR.write_text(json.dumps(pasal, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(pasal)} pasal, buku {[sum(1 for p in pasal if p['buku'] == b) for b in (1, 2, 3)]}, ganda {ganda[:10]}")
    sys.exit(1 if ganda else 0)
