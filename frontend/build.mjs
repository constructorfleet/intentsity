import { build, context } from "esbuild";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outfile = resolve(here, "../custom_components/intentsity/panel.js");
const pkg = JSON.parse(readFileSync(resolve(here, "package.json"), "utf8"));

const watch = process.argv.includes("--watch");
const checkOnly = process.argv.includes("--check");
const dev = watch || process.argv.includes("--dev");

/** @type {import('esbuild').BuildOptions} */
const options = {
  entryPoints: [resolve(here, "src/panel.jsx")],
  outfile,
  bundle: true,
  // The panel is loaded by Home Assistant as an ES module (`module_url`).
  format: "esm",
  target: ["es2022"],
  platform: "browser",
  jsx: "automatic",
  loader: { ".css": "text", ".jsx": "jsx", ".svg": "text" },
  minify: !dev,
  sourcemap: dev ? "inline" : false,
  legalComments: "none",
  define: {
    "process.env.NODE_ENV": dev ? '"development"' : '"production"',
    __INTENTSITY_VERSION__: JSON.stringify(pkg.version),
  },
  logLevel: "info",
  metafile: true,
};

if (checkOnly) {
  // Syntax and resolution check that leaves the committed panel.js untouched.
  await build({ ...options, write: false, metafile: false });
  console.log("panel sources build cleanly");
} else if (watch) {
  const ctx = await context(options);
  await ctx.watch();
  console.log("watching frontend/src → custom_components/intentsity/panel.js");
} else {
  const result = await build(options);
  const bytes = Object.values(result.metafile.outputs)[0]?.bytes ?? 0;
  console.log(`panel.js ${(bytes / 1024).toFixed(1)} KB`);
}
