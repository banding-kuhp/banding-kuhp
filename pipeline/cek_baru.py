import difflib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
WS = ROOT / "sumber" / "ws2023"
PASAL = re.compile(r"^Pasal (\d+)$")


def pasal_ws(nama):
    hasil, sekarang, judul = {}, None, False
    for b in (WS / nama).read_text().splitlines():
        b = b.strip()
        m = PASAL.match(b)
        if m:
            sekarang = hasil.setdefault(m.group(1), [])
            judul = False
            continue
        if re.match(r"^(Paragraf \d+|Bagian \w+|BAB [IVXLC]+|BUKU \w+)$", b):
            judul = True
            continue
        if judul and (b.isupper() or re.match(r"^[A-Z][\w ,/-]+$", b) and len(b) < 90 and not b.endswith((".", ";", ":"))):
            continue
        judul = False
        if sekarang is not None and b:
            sekarang.append(b)
    return hasil


def token(paragraf_list):
    teks = " ".join(paragraf_list).lower()
    teks = re.sub(r"(^|\s)(\(\d+[a-z]?\)|[a-z]\.|\d+\.)(?=\s)", " ", teks)
    teks = teks.replace("/ ", "/").replace(" /", "/")
    return re.findall(r"[a-z0-9]+", teks)


def beda(a, b):
    hasil = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            hasil.append({"llg": " ".join(a[i1:i2]), "ws": " ".join(b[j1:j2])})
    return hasil


if __name__ == "__main__":
    baru = json.loads((ROOT / "data" / "kuhp-baru.json").read_text())
    ws = {**pasal_ws("Buku_Kesatu.txt"), **pasal_ws("Buku_Kedua.txt")}
    laporan, angka = [], 0
    for p in baru:
        a, b = token(p["teks"]), token(ws.get(p["nomor"], []))
        d = beda(a, b)
        if d:
            angka_beda = [x for x in d if re.search(r"\d", x["llg"] + x["ws"])]
            angka += bool(angka_beda)
            laporan.append({"nomor": p["nomor"], "beda": d, "angka": bool(angka_beda)})
    (ROOT / "data" / "cek-baru.json").write_text(json.dumps(laporan, ensure_ascii=False, indent=1))
    print(f"{len(baru)} pasal, {len(baru) - len(laporan)} sama persis, {len(laporan)} beda, {angka} beda angka")
    for x in laporan[:25]:
        print(x["nomor"], x["beda"][:3])
