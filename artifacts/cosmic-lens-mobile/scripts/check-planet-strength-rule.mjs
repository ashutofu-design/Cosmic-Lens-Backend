import assert from "node:assert/strict";
import fs from "node:fs";
import Module from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";
import ts from "typescript";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const sourcePath = path.resolve(__dirname, "../lib/planetStrengthRule.ts");
const source = fs.readFileSync(sourcePath, "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
    esModuleInterop: true,
  },
}).outputText;

const require = Module.createRequire(import.meta.url);
const module = { exports: {} };
new Function("require", "module", "exports", compiled)(require, module, module.exports);

const {
  combinedPlanetStrength,
  evaluateNeechaBhanga,
} = module.exports;

const saturnExalted = combinedPlanetStrength(
  "Saturn",
  "Tula",
  "Tula",
  { isDebilitated: false, applies: false, reasons: [] },
  200,
);
assert.equal(saturnExalted.shortLabel, "Deep Uchch");

const marsMooltrikona = combinedPlanetStrength(
  "Mars",
  "Mesh",
  "Dhanu",
  { isDebilitated: false, applies: false, reasons: [] },
  5,
);
assert.equal(marsMooltrikona.shortLabel, "Mooltrikona");

const saturnCancelled = {
  ascendantDeg: 0,
  planets: [
    { name: "Saturn", longitude: 0, house: 1 },
    { name: "Mars", longitude: 90, house: 4 },
    { name: "Sun", longitude: 120, house: 5 },
    { name: "Moon", longitude: 150, house: 6 },
  ],
};
const nb = evaluateNeechaBhanga(saturnCancelled, "Saturn", "Mesh");
assert.equal(nb.applies, true);
assert.match(nb.reasons[0], /Mars/);
assert.equal(combinedPlanetStrength("Saturn", "Mesh", "Kumbh", nb).shortLabel, "Neech Bhanga");

const d9SupportOnly = combinedPlanetStrength(
  "Saturn",
  "Mesh",
  "Tula",
  { isDebilitated: true, applies: false, reasons: [] },
);
assert.equal(d9SupportOnly.shortLabel, "D9 Support");

const neechaVargottama = combinedPlanetStrength(
  "Saturn",
  "Mesh",
  "Mesh",
  { isDebilitated: true, applies: false, reasons: [] },
);
assert.equal(neechaVargottama.shortLabel, "Neech");

console.log("planetStrengthRule checks passed");
