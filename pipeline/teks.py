import re

AWAL = re.compile(r"^(\(\d+[a-z]?\)|[a-z]\.|\d+\.|[a-z]\))\s")
NOISE = re.compile(r"^(-\s*\d+\s*-|PRESIDEN|REPUBLIK INDONESIA|SK No\b.*)$")
LANJUT = re.compile(r"\S+\s*\.\s*\.\s*\.\s*$")


SUBJUDUL = re.compile(r"^(Ayat \(\d+[a-z]?\)|Huruf [a-z]{1,2}|Angka \d+|Pasal \d+[A-Z]?)$")


def paragraf(baris):
    hasil = []
    for b in baris:
        b = " ".join(b.split())
        if not b or NOISE.match(b) or LANJUT.fullmatch(b):
            continue
        if not hasil or AWAL.match(b) or SUBJUDUL.match(b) or hasil[-1].endswith(":") or SUBJUDUL.match(hasil[-1]):
            hasil.append(b)
        elif hasil[-1].endswith("-") and not hasil[-1].endswith(" -"):
            hasil[-1] = hasil[-1] + b
        else:
            hasil[-1] += " " + b
    return hasil


ANGKA = {"satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5, "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9,
         "sepuluh": 10, "sebelas": 11, "dua belas": 12, "tiga belas": 13, "empat belas": 14, "lima belas": 15,
         "enam belas": 16, "tujuh belas": 17, "delapan belas": 18, "sembilan belas": 19, "dua puluh": 20}
PENJARA = re.compile(
    r"(?:pidana )?(?:penjara|kurungan) (?:paling lama|selama-lamanya) "
    r"(?:(\d+) \([a-z ]+\)|([a-z ]+?)) (tahun|bulan|minggu|hari)"
    r"(?: (?:dan )?(?:(\d+) \([a-z ]+\)|([a-z ]+?)) bulan)?")


def _angka(digit, kata):
    if digit:
        return int(digit)
    kata = (kata or "").strip()
    for awal in ("pidana ", "paling lama "):
        kata = kata.removeprefix(awal)
    return ANGKA.get(kata)


def ancaman(paragraf_list):
    teks = " ".join(paragraf_list).lower()
    hasil = {"mati": "pidana mati" in teks, "seumur_hidup": "seumur hidup" in teks, "penjara_bulan": None, "denda": None}
    terlama = 0
    for m in PENJARA.finditer(teks):
        n = _angka(m.group(1), m.group(2))
        if n is None:
            continue
        bulan = {"tahun": n * 12, "bulan": n, "minggu": 0, "hari": 0}[m.group(3)]
        tambah = _angka(m.group(4), m.group(5))
        if tambah and m.group(3) == "tahun":
            bulan += tambah
        terlama = max(terlama, bulan)
    hasil["penjara_bulan"] = terlama or None
    kategori = re.findall(r"denda paling banyak kategori ([ivx]+)", teks)
    if kategori:
        urut = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"]
        hasil["denda"] = "Kategori " + max(kategori, key=lambda k: urut.index(k) if k in urut else -1).upper()
    else:
        m = re.search(r"denda paling banyak ([a-z ]+?) rupiah", teks)
        if m:
            hasil["denda"] = m.group(1).strip() + " rupiah"
    return hasil


if __name__ == "__main__":
    assert paragraf(["(1) Barang siapa", "mengambil barang.", "(2) Jika"]) == ["(1) Barang siapa mengambil barang.", "(2) Jika"]
    assert paragraf(["Diancam:", "a. pencurian;", "b. pencurian", "ternak;"]) == ["Diancam:", "a. pencurian;", "b. pencurian ternak;"]
    assert paragraf(["peraturan perundang-", "undangan pidana"]) == ["peraturan perundang-undangan pidana"]
    assert paragraf(["Huruf a", "Cukup", "jelas.", "Huruf b", "Yang dimaksud"]) == ["Huruf a", "Cukup jelas.", "Huruf b", "Yang dimaksud"]
    lama = ancaman(["Barang siapa ... diancam karena pencurian, dengan pidana penjara paling lama lima tahun atau pidana denda paling banyak sembilan ratus rupiah."])
    assert lama["penjara_bulan"] == 60 and lama["denda"] == "sembilan ratus rupiah", lama
    baru = ancaman(["dengan pidana penjara paling lama 5 (lima) tahun atau pidana denda paling banyak kategori V."])
    assert baru["penjara_bulan"] == 60 and baru["denda"] == "Kategori V", baru
    assert ancaman(["pidana penjara paling lama satu tahun empat bulan"])["penjara_bulan"] == 16
    assert ancaman(["pidana mati atau pidana penjara seumur hidup"])["mati"]
    print("teks ok")
