import json
import pathlib
import re
import sys

from teks import paragraf

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUMBER = ROOT / "sumber" / "alt" / "llg.txt"
KELUAR = ROOT / "data" / "kuhp-baru.json"
PASAL = re.compile(r"^Pasal ?(\d+)$")
BAB = re.compile(r"^BAB ([IVXLC]+[A-Z]?)$")
BUKU = re.compile(r"^BUKU (KESATU|KEDUA)$")
JUDUL = re.compile(r"^(Bagian|Paragraf) ")


def urai_batang(baris):
    hasil, buku, bab, judul_bab, sekarang, terakhir, ambil_judul, lewati_judul = [], 1, "I", [], None, 0, False, False
    for mentah in baris:
        b = " ".join(mentah.split())
        if ambil_judul:
            if b and b.isupper() and not PASAL.match(b):
                judul_bab.append(b)
                continue
            if b:
                ambil_judul = False
        if not b:
            continue
        m = BUKU.match(b)
        if m:
            buku = 1 if m.group(1) == "KESATU" else 2
            continue
        m = BAB.match(b)
        if m:
            bab, judul_bab, ambil_judul = m.group(1), [], True
            continue
        if JUDUL.match(b) and len(b) < 60:
            lewati_judul = True
            continue
        if lewati_judul and not PASAL.match(b):
            continue
        m = PASAL.match(b)
        if m and int(m.group(1)) == terakhir + 1:
            terakhir = int(m.group(1))
            lewati_judul = False
            sekarang = {"nomor": m.group(1), "buku": buku, "bab": bab, "judul_bab": " ".join(judul_bab).title(), "baris": []}
            hasil.append(sekarang)
            continue
        if sekarang:
            sekarang["baris"].append(b)
    for p in hasil:
        p["teks"] = paragraf(p.pop("baris"))
    return hasil


def urai_penjelasan(baris):
    hasil, sekarang, terakhir = {}, None, 0
    for mentah in baris:
        b = " ".join(mentah.split())
        m = PASAL.match(b)
        if m and int(m.group(1)) == terakhir + 1:
            terakhir = int(m.group(1))
            sekarang = hasil.setdefault(m.group(1), [])
            continue
        if sekarang is not None and b:
            sekarang.append(b)
    return {nomor: paragraf(isi) for nomor, isi in hasil.items()}


if __name__ == "__main__":
    baris = SUMBER.read_text(encoding="utf-8").splitlines()
    mulai_penjelasan = next(i for i, b in enumerate(baris) if b.strip() == "PENJELASAN")
    mulai_pasal = next(i for i, b in enumerate(baris) if "PASAL DEMI PASAL" in b)
    pasal = urai_batang(baris[:mulai_penjelasan])
    penjelasan = urai_penjelasan(baris[mulai_pasal:])
    for p in pasal:
        if p["nomor"] == "624":
            p["teks"] = [p["teks"][0].split(" Agar setiap orang mengetahuinya")[0]]
        isi = [b.split(" TAMBAHAN LEMBARAN NEGARA")[0] for b in penjelasan.get(p["nomor"], [])]
        p["penjelasan"] = [] if isi == ["Cukup jelas."] else isi
    KELUAR.write_text(json.dumps(pasal, ensure_ascii=False, indent=1), encoding="utf-8")
    nomor = [int(p["nomor"]) for p in pasal]
    hilang = [n for n in range(1, 625) if n not in nomor]
    print(f"{len(pasal)} pasal, buku {[sum(1 for p in pasal if p['buku'] == b) for b in (1, 2)]}, "
          f"penjelasan {sum(1 for p in pasal if p['penjelasan'])}, hilang {hilang[:20]}")
    sys.exit(1 if hilang else 0)
