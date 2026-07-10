import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const envPath = path.resolve(__dirname, "../artifacts/api-server/.env");
const text = fs.readFileSync(envPath, "utf8");
const marker = "FIREBASE_SERVICE_ACCOUNT_JSON=";
const start = text.indexOf(marker);
if (start < 0) throw new Error("FIREBASE_SERVICE_ACCOUNT_JSON not found");

const jsonStart = text.indexOf("{", start);
const jsonEnd = text.lastIndexOf("}");
const jsonText = text.slice(jsonStart, jsonEnd + 1);
const end = jsonEnd + 1;
const parsed = JSON.parse(jsonText);
const line = `${marker}${JSON.stringify(parsed)}`;
const out = text.slice(0, start) + line + text.slice(end).replace(/^\s*\n?/, "\n");
fs.writeFileSync(envPath, out.endsWith("\n") ? out : `${out}\n`);
console.log("Fixed .env — Firebase JSON is now one line.");
