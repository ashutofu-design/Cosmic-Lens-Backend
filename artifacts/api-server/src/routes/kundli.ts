import { Router, type IRouter } from "express";
import { spawn } from "child_process";
import { existsSync } from "fs";
import path from "path";

const router: IRouter = Router();

const requiredNumberFields = [
  "year",
  "month",
  "day",
  "hour",
  "minute",
  "lat",
  "lon",
  "tz",
] as const;
const requiredStringFields = ["ampm", "name", "place"] as const;

function resolvePythonScript(): string {
  if (process.env.KUNDLI_ENGINE_PATH) {
    return process.env.KUNDLI_ENGINE_PATH;
  }

  const candidates = [
    path.resolve(process.cwd(), "kundli_engine.py"),
    path.resolve(process.cwd(), "artifacts/api-server/kundli_engine.py"),
  ];
  const script = candidates.find((candidate) => existsSync(candidate));
  return script ?? candidates[0];
}

function parsePythonJson(stdout: string): unknown {
  for (const line of stdout.trim().split(/\r?\n/).reverse()) {
    if (!line.trim()) {
      continue;
    }

    try {
      return JSON.parse(line);
    } catch {
      // kundli_engine.py can emit diagnostic logs before the final JSON line.
    }
  }

  throw new Error("No JSON payload found in engine output");
}

const PYTHON_SCRIPT = resolvePythonScript();
const PYTHON_BIN =
  process.env.PYTHON_BIN ??
  process.env.PYTHON ??
  (process.platform === "win32" ? "python" : "python3");

router.post("/kundli", (req, res) => {
  const body = req.body;

  if (!body || typeof body !== "object") {
    res.status(400).json({ error: "Invalid or missing JSON body" });
    return;
  }

  const missing = [
    ...requiredNumberFields.filter((field) => typeof body[field] !== "number"),
    ...requiredStringFields.filter((field) => typeof body[field] !== "string"),
  ];
  if (missing.length > 0) {
    res.status(400).json({ error: "Missing required birth data fields", missing });
    return;
  }

  const payload = JSON.stringify({
    ...body,
    ampm: body.ampm.trim().toUpperCase(),
  });
  const py = spawn(PYTHON_BIN, [PYTHON_SCRIPT]);

  let stdout = "";
  let stderr = "";
  let responded = false;

  const respondOnce = (status: number, data: unknown): void => {
    if (responded) {
      return;
    }
    responded = true;
    res.status(status).json(data);
  };

  py.stdout.on("data", (chunk: Buffer) => {
    stdout += chunk.toString();
  });

  py.stderr.on("data", (chunk: Buffer) => {
    stderr += chunk.toString();
  });

  py.on("close", (code) => {
    if (responded) {
      return;
    }
    if (code !== 0) {
      respondOnce(500, { error: "Calculation failed", detail: stderr });
      return;
    }
    try {
      respondOnce(200, parsePythonJson(stdout));
    } catch (err) {
      respondOnce(500, {
        error: "Invalid engine output",
        detail: err instanceof Error ? err.message : String(err),
        raw: stdout,
      });
    }
  });

  py.on("error", (err) => {
    respondOnce(500, { error: "Failed to start Python", detail: err.message });
  });

  py.stdin.on("error", (err) => {
    respondOnce(500, { error: "Failed to send payload to Python", detail: err.message });
  });

  try {
    py.stdin.end(payload);
  } catch (err) {
    respondOnce(500, {
      error: "Failed to send payload to Python",
      detail: err instanceof Error ? err.message : String(err),
    });
  }
});

export default router;
