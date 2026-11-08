import { lama, baru } from "../lib/data.js";

const ringkas = (p) => p.teks.join(" ");
export function GET() {
  const data = [
    ...lama.map((p) => ({ k: "lama", n: p.nomor, b: `Bab ${p.bab} ${p.judul_bab}`, t: ringkas(p) })),
    ...baru.map((p) => ({ k: "baru", n: p.nomor, b: `Bab ${p.bab} ${p.judul_bab}`, t: ringkas(p) })),
  ];
  return new Response(JSON.stringify(data), { headers: { "Content-Type": "application/json" } });
}
