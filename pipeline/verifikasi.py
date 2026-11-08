import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BERKAS = DATA / "verifikasi.json"
JENIS = {"tetap", "diubah", "digabung", "dipecah", "dipindah", "dihapus", "baru"}
HALAMAN = (pathlib.Path(__file__).resolve().parent / "verifikasi.html").read_text(encoding="utf-8")
SITUS = os.environ.get("KUHP_SITUS", "http://127.0.0.1:4321")
BANGUN = {"jalan": False, "ok": None, "pesan": "", "waktu": ""}
KUNCI = threading.Lock()


def bangun_situs(port):
    try:
        web = ROOT / "web"
        shutil.rmtree(web / "dist-baru", ignore_errors=True)
        hasil = subprocess.run(["npx", "astro", "build", "--outDir", "./dist-baru"], cwd=web, capture_output=True, text=True,
                               timeout=600, env={**os.environ, "PUBLIC_VERIFIKASI": f"http://127.0.0.1:{port}"})
        akhir = [b for b in hasil.stdout.splitlines() if "page(s) built" in b or "rror" in b]
        if hasil.returncode == 0 and (web / "dist-baru" / "index.html").exists():
            shutil.rmtree(web / "dist-lama", ignore_errors=True)
            if (web / "dist").exists():
                os.replace(web / "dist", web / "dist-lama")
            os.replace(web / "dist-baru", web / "dist")
            shutil.rmtree(web / "dist-lama", ignore_errors=True)
        BANGUN.update(ok=hasil.returncode == 0, pesan=(akhir[-1].split("]")[-1].strip() if akhir else hasil.stderr[-300:]))
    except (OSError, subprocess.TimeoutExpired) as galat:
        BANGUN.update(ok=False, pesan=str(galat))
    BANGUN.update(jalan=False, waktu=datetime.datetime.now().strftime("%H:%M:%S"))


def baca(nama):
    return json.loads((DATA / nama).read_text(encoding="utf-8"))


def tulis(path, isi):
    sementara = path.with_suffix(".tmp")
    sementara.write_text(json.dumps(isi, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(sementara, path)


def keputusan():
    return baca("verifikasi.json") if BERKAS.exists() else {"lama": {}, "baru": {}}


def tambal_peta(kep):
    peta, baru = baca("peta.json"), baca("kuhp-baru.json")
    for e in peta:
        if not e["lama"]:
            continue
        k = kep["lama"].get(e["lama"][0])
        if k:
            e.update(baru=k["baru"], jenis=k["jenis"], catatan=k.get("catatan", ""), diverifikasi=True)
        else:
            e.update(baru=e["draft_baru"], jenis=e["draft_jenis"], catatan="", diverifikasi=False)
    peta = [e for e in peta if e["lama"]]
    asal = {n for e in peta for n in e["baru"]}
    for q in baru:
        if q["nomor"] not in asal:
            k = kep["baru"].get(q["nomor"])
            peta.append({"lama": [], "baru": [q["nomor"]], "jenis": "baru", "skor": 0, "kandidat": [],
                         "diverifikasi": bool(k), "catatan": k.get("catatan", "") if k else ""})
    tulis(DATA / "peta.json", peta)


def putuskan(isi, lama_ada, baru_ada):
    kep = keputusan()
    catatan = str(isi.get("catatan", ""))[:1000]
    if "hapus" in isi:
        kep["lama"].pop(str(isi["hapus"]), None)
        kep["baru"].pop(str(isi["hapus"]), None)
    elif "pasal_baru" in isi:
        nomor = str(isi["pasal_baru"])
        if nomor not in baru_ada:
            raise ValueError(f"Pasal {nomor} KUHP baru tidak ada")
        kep["baru"][nomor] = {"jenis": "baru", "catatan": catatan, "waktu": datetime.datetime.now().isoformat(timespec="seconds")}
    else:
        nomor, jenis = str(isi.get("lama", "")), str(isi.get("jenis", ""))
        tujuan = [str(n).strip().upper() if str(n).strip()[-1:].isalpha() else str(n).strip() for n in isi.get("baru", []) if str(n).strip()]
        if nomor not in lama_ada:
            raise ValueError(f"Pasal {nomor} KUHP lama tidak ada")
        if jenis not in JENIS - {"baru"}:
            raise ValueError("Jenis perubahan tidak dikenal")
        salah = [n for n in tujuan if n not in baru_ada]
        if salah:
            raise ValueError(f"Pasal KUHP baru tidak ada: {', '.join(salah)}")
        if jenis == "dihapus" and tujuan:
            raise ValueError("Tidak ada padanan berarti tanpa pasal baru")
        if jenis != "dihapus" and not tujuan:
            raise ValueError("Pilih minimal satu pasal KUHP baru")
        kep["lama"][nomor] = {"baru": tujuan, "jenis": jenis, "catatan": catatan,
                              "waktu": datetime.datetime.now().isoformat(timespec="seconds")}
    tulis(BERKAS, kep)
    tambal_peta(kep)
    return kep


class Penangan(BaseHTTPRequestHandler):
    def kirim(self, kode, isi, jenis="application/json"):
        data = isi.encode() if isinstance(isi, str) else json.dumps(isi, ensure_ascii=False).encode()
        self.send_response(kode)
        self.send_header("Content-Type", f"{jenis}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            return self.kirim(200, HALAMAN.replace("__SITUS__", SITUS), "text/html")
        if self.path == "/api/bangun":
            return self.kirim(200, BANGUN)
        if self.path == "/api/data":
            return self.kirim(200, {"lama": baca("kuhp-lama.json"), "baru": baca("kuhp-baru.json"),
                                    "peta": baca("peta.json"), "keputusan": keputusan()})
        self.kirim(404, {"galat": "tidak ada"})

    def do_POST(self):
        if self.path == "/api/bangun":
            with KUNCI:
                if not BANGUN["jalan"]:
                    BANGUN.update(jalan=True, ok=None, pesan="")
                    threading.Thread(target=bangun_situs, args=(self.server.server_address[1],), daemon=True).start()
            return self.kirim(200, BANGUN)
        if self.path != "/api/putus":
            return self.kirim(404, {"galat": "tidak ada"})
        panjang = int(self.headers.get("Content-Length", 0))
        if panjang > 20000:
            return self.kirim(413, {"galat": "terlalu besar"})
        try:
            isi = json.loads(self.rfile.read(panjang) or b"{}")
            lama_ada = {p["nomor"] for p in baca("kuhp-lama.json")}
            baru_ada = {p["nomor"] for p in baca("kuhp-baru.json")}
            kep = putuskan(isi, lama_ada, baru_ada)
        except (ValueError, json.JSONDecodeError) as galat:
            return self.kirim(400, {"galat": str(galat)})
        self.kirim(200, {"ok": True, "jumlah": len(kep["lama"]) + len(kep["baru"])})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    if BERKAS.exists():
        shutil.copy(BERKAS, DATA / f"verifikasi.cadangan-{datetime.date.today()}.json")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4322
    print(f"Verifikasi: http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Penangan).serve_forever()
