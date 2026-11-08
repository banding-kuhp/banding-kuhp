import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

if __name__ == "__main__":
    baru = json.loads((DATA / "kuhp-baru.json").read_text())
    butir = json.loads((DATA / "perubahan-2026.json").read_text())
    pasal = {p["nomor"]: p for p in baru}
    diterapkan = 0
    for x in butir:
        catatan = {"oleh": "UU 1/2026", "butir": x["butir"], "jenis": x["jenis"], "perintah": x["perintah"]}
        if x["jenis"] == "disisipkan":
            induk = pasal[x["pasal"].rstrip("ABCDEFGHIJ")]
            baru.insert(baru.index(induk) + 1, {"nomor": x["pasal"], "buku": induk["buku"], "bab": induk["bab"],
                                                "judul_bab": induk["judul_bab"], "teks": x["teks"], "penjelasan": [],
                                                "perubahan": [catatan], "teks_asli": []})
        elif x["pasal"] in pasal:
            p = pasal[x["pasal"]]
            p.setdefault("perubahan", []).append(catatan)
            if x["jenis"] == "penjelasan":
                p["penjelasan_diubah"] = True
                continue
            p.setdefault("teks_asli", p["teks"])
            p["teks"] = ["Dihapus."] if x["jenis"] == "dihapus" else x["teks"]
        else:
            print("pasal tidak ditemukan:", x["butir"], x["pasal"])
            continue
        diterapkan += 1
    (DATA / "kuhp-baru.json").write_text(json.dumps(baru, ensure_ascii=False, indent=1))
    print(f"{diterapkan} perubahan diterapkan, {len(baru)} pasal")
