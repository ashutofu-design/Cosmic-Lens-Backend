import { Router, type IRouter } from "express";
import { spawn } from "child_process";
import path from "path";

const router: IRouter = Router();

const PYTHON_SCRIPT = path.resolve(
  path.dirname(new URL(import.meta.url).pathname),
  "../../kundli_engine.py"
);

router.post("/kundli", (req, res) => {
  const body = req.body;
  if (
    !body ||
    typeof body.year !== "number" ||
    typeof body.month !== "number" ||
    typeof body.day !== "number" ||
    typeof body.lat !== "number" ||
    typeof body.lon !== "number"
  ) {
    res.status(400).json({ error: "Missing required birth data fields" });
    return;
  }

  const payload = JSON.stringify(body);
  const py = spawn("python3", [PYTHON_SCRIPT]);

  let stdout = "";
  let stderr = "";

  py.stdout.on("data", (chunk: Buffer) => {
    stdout += chunk.toString();
  });

  py.stderr.on("data", (chunk: Buffer) => {
    stderr += chunk.toString();
  });

  py.on("close", (code) => {
    if (code !== 0) {
      res.status(500).json({ error: "Calculation failed", detail: stderr });
      return;
    }
    try {
      const result = JSON.parse(stdout);
      res.json(result);
    } catch {
      res.status(500).json({ error: "Invalid engine output", raw: stdout });
    }
  });

  py.on("error", (err) => {
    res.status(500).json({ error: "Failed to start Python", detail: err.message });
  });

  py.stdin.write(payload);
  py.stdin.end();
});

export default router;
