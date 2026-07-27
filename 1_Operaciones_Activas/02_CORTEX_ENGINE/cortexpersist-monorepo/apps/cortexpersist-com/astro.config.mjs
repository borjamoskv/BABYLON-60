import { defineConfig } from "astro/config";

import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";
import sitemap from "@astrojs/sitemap";
import vercel from "@astrojs/vercel/serverless";

import cortexQuarantinePlugin from "./vite-plugin-cortex-quarantine.js";

// https://astro.build/config
export default defineConfig({
  site: "https://cortexpersist.com",
  output: "server",
  adapter: vercel({
    webAnalytics: {
      enabled: true,
    },
  }),
  integrations: [
    react(),
    sitemap({
      filter: (page) =>
        ![
          "/cancel/",
          "/success/",
          "/eructo/",
          "/oscilloscope/",
          "/taste/",
          "/simulation/",
          "/runtime/",
        ].some((excluded) => page.includes(excluded)),
    }),
  ],

  vite: {
    plugins: [cortexQuarantinePlugin(), tailwindcss()],
    build: {
      chunkSizeWarningLimit: 1000,
    },
    server: {
      fs: {
        allow: [".."],
      },
      proxy: {
        "/billing": "http://localhost:3005",
        "/v1": "http://localhost:3005",
      },
    },
  },
});
