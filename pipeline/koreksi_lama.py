import json
import pathlib
import re
import string

from koreksi_baru import kosakata

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HURUF = string.ascii_lowercase


def calon(kata):
    hasil = set()
    for i in range(len(kata)):
        for h in HURUF:
            if h != kata[i]:
                hasil.add(kata[:i] + h + kata[i + 1:])
    for i in range(len(kata) - 1):
        if kata[i:i + 2] == "rn":
            hasil.add(kata[:i] + "m" + kata[i + 2:])
    return hasil


KELIRU_OCR = {("c", "e"), ("e", "c"), ("s", "a"), ("i", "l"), ("l", "i"), ("o", "a"), ("h", "b"), ("v", "e"),
              ("n", "a"), ("u", "a"), ("a", "e"), ("e", "a"), ("t", "f"), ("f", "t"), ("rn", "m")}


def pasangan(dari, ke):
    if len(dari) == len(ke):
        beda = [(a, b) for a, b in zip(dari, ke) if a != b]
        return beda[0] if len(beda) == 1 else None
    return ("rn", "m") if dari.replace("rn", "m", 1) == ke else None


def perbaiki(kata, kv):
    if len(kata) < 4 or kv.get(kata, 0) > 1:
        return None, False
    pilihan = sorted(((kv[c], c) for c in calon(kata) if kv.get(c, 0) >= 8), reverse=True)
    if not pilihan or (len(pilihan) > 1 and pilihan[1][0] * 3 > pilihan[0][0]):
        return None, False
    yakin = pilihan[0][0] >= 30 and pasangan(kata, pilihan[0][1]) in KELIRU_OCR
    return pilihan[0][1], yakin


if __name__ == "__main__":
    kv = kosakata()
    lama = json.loads((DATA / "kuhp-lama.json").read_text())
    catatan, saran = [], []
    for p in lama:
        baru = []
        for par in p["teks"]:
            def tukar(m):
                kata = m.group(0)
                if par[max(0, m.start() - 1):m.start()] == "-" or par[m.end():m.end() + 1] == "-":
                    return kata
                benar, yakin = perbaiki(kata.lower(), kv)
                if not benar:
                    return kata
                if not yakin:
                    saran.append({"nomor": p["nomor"], "dari": kata, "usul": benar})
                    return kata
                catatan.append({"nomor": p["nomor"], "dari": kata, "jadi": benar})
                return benar.capitalize() if kata[0].isupper() else benar
            baru.append(re.sub(r"[A-Za-z]+", tukar, par))
        p["teks"] = baru
    (DATA / "kuhp-lama.json").write_text(json.dumps(lama, ensure_ascii=False, indent=1))
    (DATA / "koreksi-lama.json").write_text(json.dumps({"dikoreksi": catatan, "saran": saran}, ensure_ascii=False, indent=1))
    print(len(catatan), "kata dikoreksi otomatis,", len(saran), "saran untuk ditinjau")
    print("  otomatis:", ", ".join(f"{c['dari']}>{c['jadi']}" for c in catatan[:45]))
    print("  saran:", ", ".join(f"{c['nomor']}:{c['dari']}>{c['usul']}" for c in saran[:45]))
