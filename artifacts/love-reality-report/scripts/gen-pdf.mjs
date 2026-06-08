import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const apiDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../api-server");
const script = path.join(apiDir, "scripts", "gen_love_exec_preview_pdf.py");
const argv = process.argv.slice(2);

const verdictLlm = argv.includes("--verdict-llm") || process.env.LOVE_REALITY_VERDICT_PAGE_LLM === "1";
const deepAnalysisLlm =
  argv.includes("--deep-analysis-llm") || process.env.LOVE_REALITY_DEEP_ANALYSIS_LLM === "1";
const sectionsLlm =
  argv.includes("--sections-llm") ||
  argv.includes("--premium-llm") ||
  process.env.LOVE_REALITY_PREMIUM_SECTIONS === "1";
const force = argv.includes("--force");
const dev = argv.includes("--dev");
const reuse = argv.includes("--reuse");
const quality = argv.includes("--quality");

const env = { ...process.env };
if (verdictLlm) {
  env.LOVE_REALITY_VERDICT_PAGE_LLM = "1";
}
if (deepAnalysisLlm) {
  env.LOVE_REALITY_DEEP_ANALYSIS_LLM = "1";
}
if (sectionsLlm) {
  env.LOVE_REALITY_PREMIUM_SECTIONS = "1";
}
if (force && verdictLlm) {
  env.LOVE_REALITY_VERDICT_PAGE_FORCE = "1";
}
if (force && deepAnalysisLlm) {
  env.LOVE_REALITY_DEEP_ANALYSIS_FORCE = "1";
}
if (force && sectionsLlm) {
  env.LOVE_REALITY_PREMIUM_SECTIONS_FORCE = "1";
  env.LOVE_REALITY_FORCE = "1";
}
if (dev) {
  env.LOVE_REALITY_VERDICT_PAGE_DEV = "1";
  env.LOVE_REALITY_DEEP_ANALYSIS_DEV = "1";
}
if (reuse) {
  env.LOVE_REALITY_VERDICT_PAGE_REUSE_SNAPSHOT = "1";
}
if (quality) {
  env.LOVE_REALITY_VERDICT_PAGE_QUALITY = "1";
  env.LOVE_REALITY_DEEP_ANALYSIS_MODEL = env.LOVE_REALITY_DEEP_ANALYSIS_MODEL || "gpt-4o";
}

for (const py of ["python", "python3", "py"]) {
  const result = spawnSync(py, [script], {
    cwd: apiDir,
    stdio: "inherit",
    shell: process.platform === "win32",
    env,
  });
  if (result.status === 0) {
    process.exit(0);
  }
}

console.error("\nCould not run Python. Install Python 3 + reportlab, then retry: pnpm gen:pdf");
process.exit(1);
