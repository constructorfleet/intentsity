// Re-copies DesignSystem/ components and tokens into frontend/src/ds/.
// The design system is the source of truth; src/ds is a build-time vendor copy
// so the bundle has no dependency on the DesignSystem tree at runtime.
import { cp, mkdir, readdir, rm } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = resolve(here, "../DesignSystem");
const target = resolve(here, "src/ds");

for (const dir of ["components", "tokens", "assets"]) {
  await rm(join(target, dir), { recursive: true, force: true });
  await mkdir(join(target, dir), { recursive: true });
}

await cp(join(source, "components"), join(target, "components"), {
  recursive: true,
  // Docs and preview cards are authoring aids, not shippable code.
  filter: (path) => !/\.(prompt\.md|card\.html)$/.test(path),
});

for (const file of await readdir(join(source, "tokens"))) {
  if (file.endsWith(".css")) {
    await cp(join(source, "tokens", file), join(target, "tokens", file));
  }
}

// The brand marks. Only the SVGs are bundled — the PNGs under
// custom_components/intentsity/brand/ are rasterized from these separately, for
// Home Assistant's brands repository and the config-entry logo.
for (const file of await readdir(join(source, "assets"))) {
  if (file.endsWith(".svg")) {
    await cp(join(source, "assets", file), join(target, "assets", file));
  }
}

console.log(`synced ${source} → ${target}`);
