import json
import pathlib
import re
from collections import Counter

from cek_baru import beda, pasal_ws, token

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def kosakata():
    teks = " ".join([
        (ROOT / "sumber" / "alt" / "llg.txt").read_text(),
        (ROOT / "sumber" / "ws2023" / "Buku_Kesatu.txt").read_text(),
        (ROOT / "sumber" / "ws2023" / "Buku_Kedua.txt").read_text(),
        (ROOT / "sumber" / "ws2023" / "Penjelasan.txt").read_text(),
        (ROOT / "sumber" / "lama" / "kejari.txt").read_text(),
    ]).lower()
    return Counter(re.findall(r"[a-z]+", teks))


def skor(frasa, kv):
    kata = frasa.split()
    return min((kv.get(k, 0) for k in kata), default=0) if kata else -1


def ganti(paragraf_list, lama, baru):
    pola = re.compile(r"(?<![A-Za-z])" + r"[\s\-/]*".join(re.escape(k) for k in lama.split()) + r"(?![A-Za-z])", re.I)
    hasil, kena = [], 0
    for p in paragraf_list:
        def tukar(m):
            nonlocal kena
            kena += 1
            teks = baru
            return teks[0].upper() + teks[1:] if m.group(0)[0].isupper() else teks
        hasil.append(pola.sub(tukar, p, count=1) if not kena else p)
    return hasil, kena


if __name__ == "__main__":
    kv = kosakata()
    baru = json.loads((DATA / "kuhp-baru.json").read_text())
    ws = {**pasal_ws("Buku_Kesatu.txt"), **pasal_ws("Buku_Kedua.txt")}
    dikoreksi, tinjau = [], []
    for p in baru:
        for d in beda(token(p["teks"]), token(ws.get(p["nomor"], []))):
            a, b = d["llg"], d["ws"]
            if a and b and a.replace(" ", "") == b.replace(" ", ""):
                pilih = b if skor(b, kv) > skor(a, kv) else a
            elif a and b and len(a.split()) == len(b.split()) and abs(len(a) - len(b)) <= 2:
                pilih = b if skor(b, kv) > skor(a, kv) * 3 else a
            else:
                tinjau.append({"nomor": p["nomor"], "llg": a, "ws": b})
                continue
            if pilih == a:
                continue
            p["teks"], kena = ganti(p["teks"], a, b)
            (dikoreksi if kena else tinjau).append({"nomor": p["nomor"], "dari": a, "jadi": b} if kena else {"nomor": p["nomor"], "llg": a, "ws": b})
    (DATA / "kuhp-baru.json").write_text(json.dumps(baru, ensure_ascii=False, indent=1))
    (DATA / "tinjau-baru.json").write_text(json.dumps({"dikoreksi": dikoreksi, "tinjau": tinjau}, ensure_ascii=False, indent=1))
    print(f"dikoreksi {len(dikoreksi)}, perlu ditinjau {len(tinjau)}")
    for x in dikoreksi[:12]:
        print("  ", x)
    for x in tinjau[:12]:
        print("  ?", x)
