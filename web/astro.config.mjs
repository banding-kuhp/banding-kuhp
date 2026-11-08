import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://banding-kuhp.example",
  trailingSlash: "never",
  build: { format: "file" },
});
