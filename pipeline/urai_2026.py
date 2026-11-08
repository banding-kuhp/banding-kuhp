import json
import pathlib
import re

from teks import paragraf

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUMBER = ROOT / "sumber" / "uu2026" / "uu-1-2026.txt"
KELUAR = ROOT / "data" / "perubahan-2026.json"
BUTIR = re.compile(r"^\s{6,}(\d{1,2})\.\s*(\S.*)$")
JUDUL_PASAL = re.compile(r"^Pasa[l1] ?([0-9OolI]+[A-Z]?)$")
HALAMAN = re.compile(r"^-\s*[\dtlIi ]+\s*-$")


def nomor(teks):
    return re.sub(r"[OoQ]", "0", re.sub(r"[lIi|]", "1", teks)) if teks else teks


def bersih_ocr(baris):
    hasil, di_kepala = [], 0
    for mentah in baris:
        b = " ".join(mentah.split())
        if b.startswith("SK No"):
            di_kepala = 4
            continue
        if di_kepala:
            di_kepala -= 1
            if HALAMAN.match(b) or len(b) < 30:
                if HALAMAN.match(b):
                    di_kepala = 0
                continue
            di_kepala = 0
        if re.search(r"\.\s*\.\s*\.\s*$", b) and len(b) < 40:
            continue
        b = re.sub(r"\((\d)1(?=[\sA-Za-z])", r"(\1) ", b)
        b = re.sub(r"\(l\)", "(1)", b)
        b = re.sub(r"\bPasa1\b", "Pasal", b)
        b = re.sub(r"\b[Il] \(satu\)", "1 (satu)", b)
        b = re.sub(r"\(([0-9])\s+\)", r"(\1)", b)
        hasil.append((mentah, b))
    return hasil


def urai(baris):
    mulai = next(i for i, b in enumerate(baris) if b.strip() == "Pasal VII")
    akhir = next(i for i in range(mulai, len(baris)) if baris[i].strip() == "BAB IV")
    butir, sekarang = [], None
    for mentah, b in bersih_ocr(baris[mulai + 1:akhir]):
        m = BUTIR.match(mentah)
        if m and (not butir or int(m.group(1)) == butir[-1]["butir"] + 1):
            sekarang = {"butir": int(m.group(1)), "perintah": [m.group(2)], "pasal": None, "isi": []}
            butir.append(sekarang)
            continue
        if not sekarang or not b:
            continue
        j = JUDUL_PASAL.match(b)
        if j and sekarang["pasal"] is None and sekarang["perintah"][-1].rstrip().endswith((":", "berikut")):
            sekarang["pasal"] = nomor(j.group(1))
            continue
        (sekarang["isi"] if sekarang["pasal"] else sekarang["perintah"]).append(b)
    for x in butir:
        perintah = " ".join(x["perintah"])
        x["perintah"] = perintah
        x["teks"] = paragraf(x.pop("isi"))
        if x["pasal"] is None:
            m = re.search(r"Pasa[l1] ?([0-9][0-9OolI]*[A-Z]?)", perintah)
            x["pasal"] = nomor(m.group(1)) if m else None
        x["jenis"] = ("dihapus" if re.search(r"\bdihapus\.?$", perintah) and not x["teks"] else
                      "disisipkan" if "disisipkan" in perintah else
                      "penjelasan" if perintah.startswith("Penjelasan") else "diubah")
    return butir


if __name__ == "__main__":
    butir = urai(SUMBER.read_text(encoding="utf-8").splitlines())
    KELUAR.write_text(json.dumps(butir, ensure_ascii=False, indent=1))
    from collections import Counter
    print(len(butir), "butir", dict(Counter(x["jenis"] for x in butir)), "nomor terakhir", butir[-1]["butir"])
    for x in butir:
        print(f"{x['butir']:>2} {x['jenis']:<10} Pasal {x['pasal']:<5} {len(x['teks'])} par | {x['perintah'][:70]}")
