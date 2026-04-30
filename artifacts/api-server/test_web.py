"""
Standalone web test page for the Cosmic Lens AI ask flow.

Mounted at GET /api/test-web (API-server proxy claims /api/*). Designed
for browser-based smoke-testing of
the Phase 7.7-pre TRUE FULL PASSTHROUGH path (default ON since Apr 30
2026) without going through the Expo mobile client or Firebase auth.

Anonymous mode — no user_id, no api-key, no quota. The page calls
POST /api/kundli to compute a chart, then POST /api/ask with that
chart + the typed question. The response panel surfaces the `source`
field prominently so a tester can verify whether `ai_passthrough`
fired (default) vs the legacy engineered path (rollback / fallback).

Pure ADD-ONLY — flask_app.py only adds a one-line registration call.
"""

from __future__ import annotations

from flask import Response


_TEST_WEB_HTML = r"""<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Cosmic Lens — AI Passthrough Test</title>
<style>
  :root {
    --bg: #0b0e1a;
    --panel: #141a2e;
    --panel2: #1b2240;
    --border: #2a3358;
    --text: #e8ecf4;
    --muted: #8892b3;
    --accent: #f0b54a;
    --accent2: #ffd97a;
    --good: #4ade80;
    --warn: #fbbf24;
    --bad: #f87171;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0;
    background: radial-gradient(1200px 800px at 20% 0%, #1a2147 0%, var(--bg) 60%);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", sans-serif;
    min-height: 100vh;
  }
  .wrap {
    max-width: 760px;
    margin: 0 auto;
    padding: 24px 16px 80px;
  }
  header {
    text-align: center;
    margin-bottom: 18px;
  }
  header h1 {
    font-size: 24px;
    margin: 0 0 6px;
    color: var(--accent2);
    font-weight: 600;
    letter-spacing: 0.3px;
  }
  header .sub {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.5;
  }
  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 16px;
    margin-bottom: 14px;
  }
  .panel h2 {
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--muted);
    margin: 0 0 12px;
    font-weight: 600;
  }
  .row { display: flex; gap: 10px; flex-wrap: wrap; }
  .row > * { flex: 1 1 0; min-width: 90px; }
  label {
    display: block;
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 4px;
  }
  input, select, textarea {
    width: 100%;
    background: var(--panel2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 11px;
    font-size: 14px;
    font-family: inherit;
    outline: none;
  }
  input:focus, select:focus, textarea:focus { border-color: var(--accent); }
  textarea { resize: vertical; min-height: 70px; }
  .preset-chips {
    display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
  }
  .chip {
    background: var(--panel2);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 999px;
    padding: 5px 11px;
    font-size: 12px;
    cursor: pointer;
    user-select: none;
  }
  .chip:hover { border-color: var(--accent); }
  .btn-primary {
    width: 100%;
    background: linear-gradient(180deg, var(--accent2), var(--accent));
    color: #1a0f00;
    border: none;
    border-radius: 12px;
    padding: 14px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    margin-top: 6px;
    letter-spacing: 0.2px;
  }
  .btn-primary:disabled {
    opacity: 0.6; cursor: not-allowed;
  }
  .status {
    text-align: center;
    color: var(--muted);
    font-size: 13px;
    margin: 10px 0;
    min-height: 18px;
  }
  .response {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 16px;
    margin-top: 8px;
    display: none;
  }
  .response.show { display: block; }
  .badges {
    display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;
  }
  .badge {
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 600;
    letter-spacing: 0.3px;
    text-transform: uppercase;
  }
  .badge.source-passthrough {
    background: rgba(74,222,128,0.15);
    color: var(--good);
    border: 1px solid rgba(74,222,128,0.4);
  }
  .badge.source-engineered, .badge.source-other {
    background: rgba(251,191,36,0.15);
    color: var(--warn);
    border: 1px solid rgba(251,191,36,0.4);
  }
  .badge.meta {
    background: var(--panel2);
    color: var(--muted);
    border: 1px solid var(--border);
  }
  .answer {
    background: var(--panel2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    color: var(--text);
    font-size: 15px;
    line-height: 1.65;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  .error {
    background: rgba(248,113,113,0.1);
    border: 1px solid rgba(248,113,113,0.4);
    color: var(--bad);
    padding: 12px;
    border-radius: 10px;
    font-size: 13px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  .hint {
    font-size: 11px;
    color: var(--muted);
    margin-top: 4px;
  }
  details summary {
    cursor: pointer;
    color: var(--muted);
    font-size: 12px;
    margin-top: 12px;
    user-select: none;
  }
  details pre {
    margin-top: 6px;
    background: #0a0d18;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    font-size: 11px;
    color: var(--muted);
    overflow: auto;
    max-height: 200px;
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Cosmic Lens — AI Passthrough Test</h1>
    <div class="sub">
      Yeh standalone web tester hai. Real app mobile pe hai (Expo Go).<br>
      Yahan se directly /api/kundli + /api/ask hit hota hai — Firebase login bypass.
    </div>
  </header>

  <div class="panel">
    <h2>Birth Details</h2>
    <div class="row" style="margin-bottom:10px;">
      <div style="flex: 2 1 200px;">
        <label>Naam</label>
        <input id="name" type="text" value="Test User" />
      </div>
      <div>
        <label>City Preset</label>
        <select id="cityPreset">
          <option value="delhi">Delhi</option>
          <option value="mumbai">Mumbai</option>
          <option value="bangalore">Bangalore</option>
          <option value="kolkata">Kolkata</option>
          <option value="chennai">Chennai</option>
          <option value="hyderabad">Hyderabad</option>
          <option value="pune">Pune</option>
        </select>
      </div>
    </div>
    <div class="row" style="margin-bottom:10px;">
      <div><label>Day</label><input id="day" type="number" min="1" max="31" value="15" /></div>
      <div><label>Month</label><input id="month" type="number" min="1" max="12" value="8" /></div>
      <div><label>Year</label><input id="year" type="number" min="1900" max="2100" value="1990" /></div>
    </div>
    <div class="row">
      <div><label>Hour</label><input id="hour" type="number" min="1" max="12" value="7" /></div>
      <div><label>Minute</label><input id="minute" type="number" min="0" max="59" value="30" /></div>
      <div>
        <label>AM/PM</label>
        <select id="ampm">
          <option value="AM">AM</option>
          <option value="PM">PM</option>
        </select>
      </div>
    </div>
    <div class="hint">Latitude/Longitude/Timezone city preset se auto-fill hoga.</div>
  </div>

  <div class="panel">
    <h2>Sawaal</h2>
    <textarea id="question" placeholder="Apna prashn yahan likho..."
      >Meri shaadi kab hogi aur jeevan-saathi kaisa milega?</textarea>
    <div class="preset-chips">
      <span class="chip" data-q="Meri shaadi kab hogi aur jeevan-saathi kaisa milega?">Shaadi yog</span>
      <span class="chip" data-q="Mera career next 5 saal mein kaisa rahega?">Career 5 saal</span>
      <span class="chip" data-q="Mujhe paisa kab tak milega? Dhan yog hai meri kundli mein?">Dhan yog</span>
      <span class="chip" data-q="Meri sehat kaisi rahegi? Koi rog ka khatra to nahi?">Sehat</span>
      <span class="chip" data-q="Meri kundli mein Mangal Dosh hai kya?">Mangal Dosh</span>
      <span class="chip" data-q="Meri kundli mein Sade-Sati chal rahi hai kya?">Sade-Sati</span>
      <span class="chip" data-q="Mere ghar pariwar mein sukh shanti rahegi?">Pariwar</span>
      <span class="chip" data-q="Videsh yatra ka yog hai kya meri kundli mein?">Videsh yog</span>
    </div>
  </div>

  <button id="goBtn" class="btn-primary">Get Reading</button>
  <div id="status" class="status"></div>

  <div id="response" class="response">
    <div id="badges" class="badges"></div>
    <div id="answer" class="answer"></div>
    <details>
      <summary>Raw response (debug)</summary>
      <pre id="raw"></pre>
    </details>
  </div>
</div>

<script>
(function(){
  // Indian cities — lat, lon, tz (always 5.5 for India), display place name
  var CITIES = {
    delhi:     { lat: 28.6139, lon: 77.2090, tz: 5.5, place: "New Delhi, India" },
    mumbai:    { lat: 19.0760, lon: 72.8777, tz: 5.5, place: "Mumbai, India" },
    bangalore: { lat: 12.9716, lon: 77.5946, tz: 5.5, place: "Bengaluru, India" },
    kolkata:   { lat: 22.5726, lon: 88.3639, tz: 5.5, place: "Kolkata, India" },
    chennai:   { lat: 13.0827, lon: 80.2707, tz: 5.5, place: "Chennai, India" },
    hyderabad: { lat: 17.3850, lon: 78.4867, tz: 5.5, place: "Hyderabad, India" },
    pune:      { lat: 18.5204, lon: 73.8567, tz: 5.5, place: "Pune, India" }
  };

  var $ = function(id){ return document.getElementById(id); };
  var goBtn = $("goBtn");
  var statusEl = $("status");
  var responseEl = $("response");
  var badgesEl = $("badges");
  var answerEl = $("answer");
  var rawEl = $("raw");

  // Question chips → fill textarea
  document.querySelectorAll(".chip").forEach(function(chip){
    chip.addEventListener("click", function(){
      $("question").value = chip.getAttribute("data-q") || "";
      $("question").focus();
    });
  });

  function setStatus(msg, kind){
    statusEl.textContent = msg || "";
    statusEl.style.color = kind === "err" ? "var(--bad)" :
                           kind === "ok"  ? "var(--good)" :
                                            "var(--muted)";
  }

  function showError(label, detail){
    badgesEl.innerHTML = '<span class="badge meta">ERROR</span>';
    answerEl.innerHTML = '<div class="error">' +
      label + (detail ? "\n\n" + detail : "") + '</div>';
    rawEl.textContent = detail || "";
    responseEl.classList.add("show");
  }

  function showResponse(askJson, totalMs){
    var src = askJson.source || "unknown";
    var srcClass = src === "ai_passthrough" ? "source-passthrough" :
                   src === "ai_engineered" ? "source-engineered" :
                                              "source-other";
    var srcLabel = src === "ai_passthrough" ? "PASSTHROUGH (pure AI)" :
                   src === "brand_guard"    ? "BRAND GUARD (off-topic)" :
                   src === "shortcut"       ? "SHORTCUT (canned)" :
                                              ("SOURCE: " + src);

    var conf = (typeof askJson.confidence === "number")
      ? Math.round(askJson.confidence * 100) + "% conf" : "";
    var topic = askJson.topic ? ("topic: " + askJson.topic) : "";
    var time = (totalMs/1000).toFixed(1) + "s";

    var badges = ['<span class="badge ' + srcClass + '">' + srcLabel + '</span>'];
    if (topic) badges.push('<span class="badge meta">' + topic + '</span>');
    if (conf)  badges.push('<span class="badge meta">' + conf + '</span>');
    badges.push('<span class="badge meta">' + time + '</span>');

    badgesEl.innerHTML = badges.join("");
    answerEl.textContent = askJson.text || "(empty response)";
    rawEl.textContent = JSON.stringify(askJson, null, 2);
    responseEl.classList.add("show");
  }

  async function postJson(path, body){
    var r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    var txt = await r.text();
    var json = null;
    try { json = JSON.parse(txt); } catch(e){}
    return { ok: r.ok, status: r.status, json: json, raw: txt };
  }

  goBtn.addEventListener("click", async function(){
    var q = ($("question").value || "").trim();
    if (!q) { setStatus("Sawaal toh likho pehle.", "err"); return; }

    var city = CITIES[$("cityPreset").value] || CITIES.delhi;
    var birthPayload = {
      name: $("name").value || "Test User",
      day: parseInt($("day").value, 10),
      month: parseInt($("month").value, 10),
      year: parseInt($("year").value, 10),
      hour: parseInt($("hour").value, 10),
      minute: parseInt($("minute").value, 10),
      ampm: $("ampm").value,
      lat: city.lat,
      lon: city.lon,
      tz: city.tz,
      place: city.place
    };

    goBtn.disabled = true;
    responseEl.classList.remove("show");
    badgesEl.innerHTML = "";
    answerEl.textContent = "";

    var t0 = performance.now();

    try {
      // Step 1 — compute chart
      setStatus("Kundli bana raha hoon...", "");
      var k = await postJson("/api/kundli", birthPayload);
      if (!k.ok) {
        showError("Kundli compute fail (HTTP " + k.status + ")", k.raw);
        setStatus("Kundli error.", "err");
        return;
      }
      var chart = k.json;

      // Step 2 — ask AI
      setStatus("AI se jawab maang raha hoon... (10-30 sec)", "");
      var a = await postJson("/api/ask", {
        question: q,
        kundli: chart,
        birthData: birthPayload,
        lang: "hn",
        replyIdx: 0,
        history: []
      });
      if (!a.ok) {
        showError("AI ask fail (HTTP " + a.status + ")", a.raw);
        setStatus("AI error.", "err");
        return;
      }

      var totalMs = performance.now() - t0;
      showResponse(a.json, totalMs);
      setStatus("Done.", "ok");

    } catch (err) {
      showError("Network / unexpected error", String(err && err.stack || err));
      setStatus("Error.", "err");
    } finally {
      goBtn.disabled = false;
    }
  });

  setStatus("Ready. Defaults set hain — Get Reading dabao.");
})();
</script>
</body>
</html>
"""


def register_test_web(app) -> None:
    """Mount GET /api/test-web on the given Flask app.

    Path is under /api/* because the global reverse proxy routes /api/*
    to this service (see .replit-artifact/artifact.toml). A bare
    /test-web would land on the wrong artifact.
    """
    @app.route("/api/test-web", methods=["GET"])
    def _test_web_page():
        return Response(_TEST_WEB_HTML, mimetype="text/html; charset=utf-8")
