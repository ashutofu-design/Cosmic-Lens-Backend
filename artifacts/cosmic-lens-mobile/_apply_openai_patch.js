const fs = require("fs");
const path = require("path");

const target = path.join(__dirname, "..", "api-server", "openai_helper.py");
const report = path.join(__dirname, "openai_helper_patch_report.txt");

function isCommitmentIfStart(lines, i) {
  if (i >= lines.length || lines[i].trimEnd() !== "if (") return false;
  const chunk = lines.slice(i, Math.min(i + 6, lines.length)).join("");
  return (
    chunk.includes("_is_mr_static") &&
    chunk.includes("_mr_engine_result is not None") &&
    chunk.includes("archetype") &&
    chunk.toLowerCase().includes("commitment")
  );
}

function findHumanStart(lines) {
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (
      line.includes("Commitment engine") &&
      line.includes("deterministic template narrator") &&
      line.includes("production")
    ) {
      return i;
    }
  }
  return -1;
}

function blockEndFrom(lines, start) {
  const base = lines[start].length - lines[start].trimStart().length;
  let i = start + 1;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i++;
      continue;
    }
    const indent = line.length - line.trimStart().length;
    if (indent <= base && !line.trimStart().startsWith("#")) break;
    i++;
  }
  return Math.max(start, i - 1);
}

let text = fs.readFileSync(target, "utf8");
const origLines = text.split("\n");
const orig = origLines.length;

const templateIdx = origLines.findIndex(
  (l) => l.includes("MR engine template-only") && l.includes("manglik")
);
if (templateIdx < 0) throw new Error("template marker not found");

let deleteStart = -1;
for (let i = 0; i < origLines.length; i++) {
  if (isCommitmentIfStart(origLines, i)) {
    deleteStart = i;
    break;
  }
}
if (deleteStart < 0) throw new Error("commitment if block not found");

const humanStart = findHumanStart(origLines);
let humanEnd = -1;
if (humanStart >= 0) {
  for (let j = humanStart; j < Math.min(humanStart + 50, origLines.length); j++) {
    if (
      origLines[j].includes("human_narrator_enabled()") &&
      origLines[j].includes("_is_mr_static")
    ) {
      humanEnd = blockEndFrom(origLines, j);
      break;
    }
  }
}

let newLines;
let mode;
if (
  humanStart >= 0 &&
  humanEnd >= humanStart &&
  deleteStart <= humanStart &&
  humanStart < templateIdx
) {
  newLines = [
    ...origLines.slice(0, deleteStart),
    ...origLines.slice(humanStart, humanEnd + 1),
    ...origLines.slice(templateIdx),
  ];
  mode = "splice_keep_human";
} else {
  newLines = [...origLines.slice(0, deleteStart), ...origLines.slice(templateIdx)];
  mode = "contiguous";
}

text = newLines.join("\n");
const blockRemoved = orig - newLines.length;

let imp = 0;
text = text
  .split("\n")
  .filter((line) => {
    const st = line.trimStart();
    if (
      line.includes("commitment_narrator") &&
      (st.startsWith("import ") || st.startsWith("from "))
    ) {
      imp++;
      return false;
    }
    return true;
  })
  .join("\n");

const valStart = text.indexOf(
  '            if _archetype_mr == "commitment" and _mr_engine_result is not None:'
);
let valRemoved = 0;
if (valStart >= 0) {
  const endMarker = "lang=eff_lang,\n                    )";
  const end = text.indexOf(endMarker, valStart);
  if (end >= 0) {
    const endLine = text.indexOf("\n", end + endMarker.length);
    const sliceEnd = endLine >= 0 ? endLine : text.length;
    valRemoved = text.slice(valStart, sliceEnd).split("\n").length;
    text = text.slice(0, valStart) + text.slice(sliceEnd);
  }
}

const oldPn =
  '            if _mr_rec_result.archetype == "partner_nature":\n' +
  "                from ask_mr.engines.partner_nature import partner_nature_narrator_payload\n\n" +
  "                chart_text = partner_nature_narrator_payload(_mr_rec_result)\n" +
  "            else:\n" +
  "                chart_text = _mr_rec_result.to_narrator_payload()";
const newPn =
  '            if _mr_rec_result.archetype == "partner_nature":\n' +
  "                from ask_mr.relationship_narrator import attach_narrator_json_to_result\n\n" +
  "                attach_narrator_json_to_result(\n" +
  "                    _mr_rec_result,\n" +
  '                    question=question or "",\n' +
  "                    llm_intent=_llm_intent_admin if isinstance(_llm_intent_admin, dict) else None,\n" +
  "                )\n" +
  "            chart_text = _mr_rec_result.to_narrator_payload()";

let pnn = 0;
if (text.includes(oldPn)) {
  text = text.replace(oldPn, newPn);
  pnn = 1;
} else {
  pnn = (text.match(/partner_nature_narrator_payload/g) || []).length;
  text = text.replace(/partner_nature_narrator_payload/g, "to_narrator_payload");
}

fs.writeFileSync(target, text, "utf8");
const final = text.split("\n").length;

const lines = [
  `mode=${mode}`,
  `orig_lines=${orig}`,
  `delete_start=${deleteStart + 1}`,
  `template_idx=${templateIdx + 1}`,
  `human_start=${humanStart >= 0 ? humanStart + 1 : "null"}`,
  `human_end=${humanEnd >= 0 ? humanEnd + 1 : "null"}`,
  `lines_removed_block=${blockRemoved}`,
  `commitment_narrator_imports_removed=${imp}`,
  `commitment_llm_validation_lines_removed=${valRemoved}`,
  `partner_nature_replacements=${pnn}`,
  `final_lines=${final}`,
  `lines_removed_total=${orig - final}`,
];
fs.writeFileSync(report, lines.join("\n") + "\n", "utf8");
console.log(lines.join("\n"));
