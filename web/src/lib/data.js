import fs from "node:fs";
import path from "node:path";

const DATA = path.resolve(process.cwd(), "../data");
const baca = (nama) => JSON.parse(fs.readFileSync(path.join(DATA, nama), "utf-8"));

export const lama = baca("kuhp-lama.json");
export const baru = baca("kuhp-baru.json");
export const peta = baca("peta.json");
const bacaJika = (nama, awal) => (fs.existsSync(path.join(DATA, nama)) ? baca(nama) : awal);
export const tinjauBaru = bacaJika("tinjau-baru.json", { dikoreksi: [], tinjau: [] });
export const koreksiLama = bacaJika("koreksi-lama.json", { dikoreksi: [], saran: [] });
export const pasalLama = new Map(lama.map((p) => [p.nomor, p]));
export const pasalBaru = new Map(baru.map((p) => [p.nomor, p]));

export const dariLama = (nomor) => peta.filter((e) => e.lama.includes(nomor));
export const keBaru = (nomor) => peta.filter((e) => e.baru.includes(nomor));

export const KATEGORI = Object.fromEntries(
  [...(pasalBaru.get("79")?.teks.join(" ") ?? "").matchAll(/kategori ([IVX]+), (Rp[\d.]+),00/g)].map((m) => [m[1], m[2]]),
);

export const JENIS = {
  tetap: "Tetap",
  diubah: "Diubah",
  digabung: "Digabung",
  dipecah: "Dipecah",
  dipindah: "Dipindah",
  dihapus: "Tidak ada padanan",
  baru: "Pasal baru",
};

export const BUKU_LAMA = { 1: "Buku Kesatu: Aturan Umum", 2: "Buku Kedua: Kejahatan", 3: "Buku Ketiga: Pelanggaran" };
export const BUKU_BARU = { 1: "Buku Kesatu: Aturan Umum", 2: "Buku Kedua: Tindak Pidana" };

export function lamaWaktu(bulan) {
  if (!bulan) return null;
  const tahun = Math.floor(bulan / 12);
  const sisa = bulan % 12;
  return [tahun && `${tahun} tahun`, sisa && `${sisa} bulan`].filter(Boolean).join(" ");
}

export function ringkasAncaman(a) {
  if (!a) return "Tidak disebut";
  const bagian = [];
  if (a.mati) bagian.push("pidana mati");
  if (a.seumur_hidup) bagian.push("penjara seumur hidup");
  if (a.penjara_bulan) bagian.push(`penjara paling lama ${lamaWaktu(a.penjara_bulan)}`);
  if (a.denda) bagian.push(`denda paling banyak ${a.denda.startsWith("Kategori") ? `${a.denda} (${KATEGORI[a.denda.split(" ")[1]] ?? "?"})` : a.denda}`);
  return bagian.length ? bagian.join(", ") : "Tidak disebut";
}

export function arahPenjara(dulu, kini) {
  if (!dulu?.penjara_bulan || !kini?.penjara_bulan) return null;
  if (kini.penjara_bulan > dulu.penjara_bulan) return "naik";
  if (kini.penjara_bulan < dulu.penjara_bulan) return "turun";
  return "sama";
}

export const urutNomor = (a, b) => parseInt(a, 10) - parseInt(b, 10) || a.localeCompare(b);
