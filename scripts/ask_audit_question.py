#!/usr/bin/env python3
"""Run one Ask question on VPS (Demo User) and audit the admin row.

Usage (from repo root):
  python scripts/ask_audit_question.py "mera baby kab hoga"
  python scripts/ask_audit_question.py "car konsa colour best hoga buy karne me" --lang hi

Env (optional):
  ASK_AUDIT_API_BASE   default http://187.127.174.55:8080
  ADMIN_SECRET         or read from artifacts/admin-web/.env (VITE_ADMIN_SECRET)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API = (os.environ.get("ASK_AUDIT_API_BASE") or "http://187.127.174.55:8080").rstrip("/")


def _read_admin_secret() -> str:
    if os.environ.get("ADMIN_SECRET", "").strip():
        return os.environ["ADMIN_SECRET"].strip()
    for rel in (
        "artifacts/admin-web/.env",
        "artifacts/api-server/.env",
    ):
        p = ROOT / rel
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("VITE_ADMIN_SECRET="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
            if line.startswith("ADMIN_SECRET="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _http(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict | None = None,
    timeout: int = 120,
) -> tuple[int, Any]:
    data = None
    hdrs = {"Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw) if raw.strip() else {"error": raw}
        except json.JSONDecodeError:
            return exc.code, {"error": raw}


def _demo_login() -> dict[str, Any]:
    code, data = _http("POST", f"{DEFAULT_API}/api/auth/demo", body={})
    if code != 200 or not isinstance(data, dict) or not data.get("api_key"):
        raise RuntimeError(f"demo login failed HTTP {code}: {data}")
    return data


def _user_kundli(user_id: int, api_key: str) -> tuple[dict, dict]:
    code, data = _http(
        "GET",
        f"{DEFAULT_API}/api/user/{user_id}/kundli",
        headers={"X-User-Id": str(user_id), "X-API-Key": api_key},
    )
    if code != 200 or not isinstance(data, dict):
        raise RuntimeError(f"kundli fetch failed HTTP {code}: {data}")
    k = data.get("kundli") or {}
    chart = k.get("chart_data") if isinstance(k.get("chart_data"), dict) else {}
    birth = {
        "year": k.get("birth_year") or chart.get("birth_year"),
        "month": k.get("birth_month") or chart.get("birth_month"),
        "day": k.get("birth_day") or chart.get("birth_day"),
        "hour": k.get("birth_hour") or chart.get("birth_hour"),
        "minute": k.get("birth_minute") or chart.get("birth_minute"),
        "place": k.get("birth_place") or chart.get("birth_place") or "Delhi",
        "timezone": k.get("timezone") or chart.get("timezone") or "Asia/Kolkata",
    }
    kundli = chart if chart.get("planets") else chart
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        raise RuntimeError("Demo user has no chart — open app once and save kundli.")
    return kundli, birth


def _ask_stream(
    question: str,
    lang: str,
    user_id: int,
    api_key: str,
    kundli: dict,
    birth: dict,
) -> dict[str, Any]:
    payload = {
        "question": question,
        "lang": lang,
        "kundli": kundli,
        "birth": birth,
    }
    headers = {
        "Content-Type": "application/json",
        "X-User-Id": str(user_id),
        "X-API-Key": api_key,
    }
    # Prefer sync /api/ask — simpler + same DB save for admin.
    code, sync_out = _http(
        "POST",
        f"{DEFAULT_API}/api/ask",
        headers=headers,
        body=payload,
        timeout=180,
    )
    if code == 200 and isinstance(sync_out, dict) and sync_out.get("text"):
        return sync_out

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{DEFAULT_API}/api/ask/stream",
        data=data,
        headers=headers,
        method="POST",
    )
    final: dict[str, Any] = {}
    last_text = ""
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if not raw:
                    continue
                try:
                    evt = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if evt.get("error"):
                    raise RuntimeError(str(evt.get("error")))
                if evt.get("done"):
                    final = evt
                    break
                if evt.get("delta"):
                    last_text += str(evt.get("delta") or "")
                if evt.get("text"):
                    last_text = str(evt.get("text") or "")
    except Exception as stream_exc:
        # Retry once via sync path; avoids "Remote end closed connection..."
        # breaking full-audit runs.
        try:
            code2, sync_out2 = _http(
                "POST",
                f"{DEFAULT_API}/api/ask",
                headers=headers,
                body=payload,
                timeout=240,
            )
            if code2 == 200 and isinstance(sync_out2, dict) and sync_out2.get("text"):
                return sync_out2
        except Exception:
            pass
        raise stream_exc
    if not final and last_text.strip():
        final = {"text": last_text.strip(), "topic": "general", "source": "stream_partial"}
    if not final:
        raise RuntimeError("stream ended without done event")
    return final


def _admin_latest(user_id: int, admin_token: str, question: str) -> dict | None:
    time.sleep(1.5)
    code, listing = _http(
        "GET",
        f"{DEFAULT_API}/api/admin/ask-questions?user_id={user_id}&per_page=10&page=1",
        headers={"X-Admin-Token": admin_token},
    )
    if code != 200 or not isinstance(listing, dict):
        return None
    qnorm = question.strip().lower()
    for item in listing.get("items") or []:
        if not isinstance(item, dict):
            continue
        qt = str(item.get("question_text") or "").strip().lower()
        if qt == qnorm or qnorm in qt:
            qid = item.get("id")
            if not qid:
                return item
            code2, detail = _http(
                "GET",
                f"{DEFAULT_API}/api/admin/ask-questions/{qid}",
                headers={"X-Admin-Token": admin_token},
            )
            if code2 == 200 and isinstance(detail, dict):
                return detail
            return item
    items = listing.get("items") or []
    return items[0] if items else None


def _extract_engine_context(admin_row: dict | None) -> dict[str, Any]:
    ctx: dict[str, Any] = {}
    if not admin_row or not isinstance(admin_row.get("llm_context"), dict):
        return ctx
    raw = admin_row["llm_context"]
    blocks = raw.get("blocks") or {}
    trace = blocks.get("engine_trace") or {}
    sm = raw.get("slice_meta") or {}
    engine_facts = raw.get("engine_facts") if isinstance(raw.get("engine_facts"), dict) else {}
    ctx["engine"] = str(trace.get("engine") or sm.get("slice") or engine_facts.get("engine") or "")
    ctx["qtype"] = str(raw.get("question_type") or raw.get("checks", {}).get("slice_type") or "")
    ctx["archetype"] = str(
        sm.get("archetype") or trace.get("archetype") or engine_facts.get("archetype") or ""
    )
    ctx["verdict"] = str(sm.get("verdict") or trace.get("verdict") or engine_facts.get("verdict") or "")
    ev = (
        sm.get("evidence")
        or trace.get("evidence")
        or engine_facts.get("evidence")
        or trace.get("factors")
        or []
    )
    ctx["evidence"] = [str(x) for x in ev if x]
    ctx["summary"] = [str(x) for x in (sm.get("summary") or trace.get("summary") or []) if x]
    ctx["step_audit"] = trace.get("step_audit") or sm.get("step_audit") or {}
    ctx["narrator_mode"] = str(
        sm.get("narrator_mode") or raw.get("checks", {}).get("narrator_mode") or ""
    )
    ctx["llm_called"] = raw.get("llm_called")
    ctx["skip_reason"] = str(raw.get("skip_reason") or "")
    return ctx


def _classify_answer_path(source: str, engine: str, engine_tag: str) -> str:
    src = (source or "").strip().lower()
    if src == "direct_llm_no_engine" or "llm_no_engine" in src:
        return "direct_llm_no_engine"
    if "engine_then_llm" in src or src.startswith("raw_passthrough_"):
        if engine:
            return f"engine_then_llm ({engine})"
        return "engine_then_llm"
    if engine and not src:
        return f"engine ({engine})"
    if engine_tag == "ans-engine":
        return f"engine_path ({engine or 'unknown'})"
    return source or "unknown"


def _check_evidence_vs_answer(
    question: str,
    answer: str,
    engine_ctx: dict[str, Any],
) -> dict[str, Any]:
    """Light sanity: engine ran, evidence present, answer not contradicting locked pick."""
    checks: list[str] = []
    warnings: list[str] = []
    engine = engine_ctx.get("engine") or ""
    evidence = engine_ctx.get("evidence") or []
    verdict = engine_ctx.get("verdict") or ""
    summary = engine_ctx.get("summary") or []
    ans_l = answer.lower()

    if engine:
        checks.append(f"admin_engine={engine}")
    else:
        warnings.append("NO_ADMIN_ENGINE — admin row me engine slice missing")

    if evidence:
        checks.append(f"evidence_lines={len(evidence)}")
    elif engine and not engine.endswith("_timing_v1"):
        warnings.append("NO_ENGINE_EVIDENCE — engine chala lekin evidence empty")

    locked_pick = ""
    for line in summary:
        if "LOCKED_PICK:" in line:
            locked_pick = line.split("LOCKED_PICK:", 1)[1].strip()
            break
    if not locked_pick and "best=" in verdict:
        try:
            locked_pick = verdict.split("best=")[1].split()[0]
        except Exception:
            pass

    if locked_pick:
        checks.append(f"locked_pick={locked_pick}")
        pick_colour = locked_pick.split()[0].lower()
        if pick_colour and pick_colour not in ans_l and pick_colour not in ("primary", "alternate"):
            # For comparison Qs winner should appear in answer
            if re.search(r"\b(black|white|red|safed|kala)\b", question, re.I):
                mentioned = re.findall(r"\b(black|white|red|safed|kala|lal)\b", question, re.I)
                winner_in_ans = any(m.lower() in ans_l for m in mentioned)
                if not winner_in_ans and not any(c in ans_l for c in ("white", "black", "safed", "kala")):
                    warnings.append(
                        f"ANSWER_MAY_DRIFT — locked pick {locked_pick!r} answer me clearly nahi dikha"
                    )

    if "vehicle_colour" in (engine_ctx.get("archetype") or ""):
        if "jupiter" in ans_l and not any("jupiter" in e.lower() for e in evidence):
            warnings.append(
                "GENERIC_PLANET_DRIFT — answer Jupiter bol raha hai lekin engine evidence me nahi"
            )
        if engine and "vehicle_engine" not in engine:
            warnings.append(f"WRONG_SLICE — colour Q par engine={engine}")

    if re.search(r"\bkab\b", question, re.I):
        step_audit = engine_ctx.get("step_audit") or {}
        if engine.endswith("_timing_v1") and not step_audit:
            warnings.append("MISSING_STEP_AUDIT — timing engine par step audit nahi")

    return {
        "locked_pick": locked_pick or None,
        "evidence_sample": evidence[:5],
        "checks": checks,
        "warnings": warnings,
        "evidence_ok": bool(evidence) and not any(
            w.startswith("NO_ENGINE") or w.startswith("GENERIC_PLANET") for w in warnings
        ),
    }


def _audit(question: str, ask_out: dict, admin_row: dict | None) -> dict[str, Any]:
    issues: list[str] = []
    ok: list[str] = []
    topic = str(ask_out.get("topic") or admin_row.get("topic") if admin_row else "")
    source = str(ask_out.get("source") or admin_row.get("answer_source") if admin_row else "")
    engine_tag = str(ask_out.get("engine_tag") or (admin_row or {}).get("engine_tag") or "")
    text = str(ask_out.get("text") or (admin_row or {}).get("answer_text") or "").strip()

    engine_ctx = _extract_engine_context(admin_row)
    engine = engine_ctx.get("engine") or ""
    qtype = engine_ctx.get("qtype") or ""
    answer_path = _classify_answer_path(source, engine, engine_tag)
    evidence_audit = _check_evidence_vs_answer(question, text, engine_ctx)

    if not text:
        issues.append("NO_ANSWER — jawab empty")
    else:
        ok.append(f"answer_len={len(text)}")

    if topic == "off_topic" or source.startswith("scope_gate"):
        issues.append(f"BLOCKED — topic={topic} source={source}")
    elif "engine_required" in source or "refusal" in source.lower():
        issues.append(f"ENGINE_REFUSAL — source={source}")
    else:
        ok.append(f"topic={topic or '?'}")

    if source == "direct_llm_no_engine" or answer_path == "direct_llm_no_engine":
        issues.append(
            f"DIRECT_LLM — engine facts inject nahi hue; path={answer_path} source={source}"
        )
    elif "engine_then_llm" in answer_path or "engine_path" in answer_path:
        ok.append(f"answer_path={answer_path}")
        ok.append(f"engine_tag={engine_tag or '?'}")

    if evidence_audit["warnings"]:
        issues.extend(evidence_audit["warnings"])
    if evidence_audit["checks"]:
        ok.extend(evidence_audit["checks"])
    if evidence_audit.get("evidence_ok"):
        ok.append("chart_evidence_ok")

    if re.search(r"\bkab\b", question, re.I):
        if qtype == "STATIC" and "timing" not in engine:
            issues.append(f"TIMING_Q_BUT_STATIC — engine={engine} qtype={qtype}")
        elif "timing" in engine or engine.endswith("_timing_v1"):
            ok.append(f"timing_engine={engine}")
        elif engine:
            issues.append(f"TIMING_Q_UNEXPECTED_ENGINE — {engine}")

    step_audit = engine_ctx.get("step_audit") or {}
    if engine.endswith("_timing_v1") and not step_audit:
        issues.append("MISSING_STEP_AUDIT — deploy latest API + re-ask")

    if "baby" in question.lower() or "bach" in question.lower():
        if "health_engine" in engine:
            issues.append("WRONG_ENGINE — baby Q routed to health_engine_v1")
        if "children_timing" in engine or engine == "children_timing_v1":
            ok.append("children_timing_v1")

    if re.search(r"\b(shubh\s*samay|approach|pasand|ladki)\b", question, re.I):
        if "love_timing" in engine or engine == "love_timing_v1":
            ok.append(f"love_timing_engine={engine}")
        elif source == "mr_engine_then_llm" and re.search(
            r"\b(abhi|samay|shubh)\b", question, re.I
        ):
            issues.append(
                "WRONG_ENGINE — love approach timing Q routed to mr_engine static, not love_timing_v1"
            )

    if re.search(r"\b(numerolog|naam|name).{0,40}\b(sahi|change|badal)\b", question, re.I):
        if "numerology_engine" in engine:
            ok.append(f"numerology_engine={engine}")
            if engine_ctx.get("archetype") in ("name_correction", "name_harmony"):
                ok.append(f"archetype={engine_ctx.get('archetype')}")
        elif source == "direct_llm_no_engine" or not engine:
            issues.append("WRONG_PATH — numerology naam Q par engine slice missing")
        checks_data = (admin_row or {}).get("llm_context", {}).get("slice_meta", {}).get("checks", {})
        if not checks_data and isinstance(admin_row, dict):
            sm = (admin_row.get("llm_context") or {}).get("slice_meta") or {}
            checks_data = sm.get("checks") or {}
        if checks_data.get("driver") and checks_data.get("conductor"):
            ok.append(
                f"driver={checks_data.get('driver')} conductor={checks_data.get('conductor')} "
                f"harmony={checks_data.get('harmony_score')}"
            )
        elif engine.endswith("numerology_engine_v1"):
            issues.append("MISSING_NUMEROLOGY_CHECKS — driver/conductor admin me nahi")

    if re.search(r"\b(car|gaadi|colour|color|black|white)\b", question, re.I):
        if "property_timing" in engine or "property_engine" in engine:
            issues.append("WRONG_ENGINE — vehicle/colour Q routed to property")
        if "vehicle" in engine:
            ok.append(f"vehicle_engine={engine}")
        if re.search(r"\b(colou?r|black|white|safed|kala|rang)\b", question, re.I):
            if engine_ctx.get("archetype") == "vehicle_colour":
                ok.append("archetype=vehicle_colour")
            elif "vehicle_engine" in engine and engine_ctx.get("archetype") != "vehicle_colour":
                issues.append(
                    f"COLOUR_Q_WRONG_ARCH — archetype={engine_ctx.get('archetype') or '?'}"
                )

    if "BCP" in str(step_audit.get("step1", {}).get("name", "")) and "property" in engine:
        ok.append("property BCP step1 present")

    return {
        "question": question,
        "api_base": DEFAULT_API,
        "ask_topic": topic,
        "ask_source": source,
        "engine_tag": engine_tag,
        "answer_path": answer_path,
        "answer_text": text,
        "admin_id": (admin_row or {}).get("id"),
        "admin_engine": engine,
        "admin_archetype": engine_ctx.get("archetype") or None,
        "admin_qtype": qtype,
        "admin_verdict": engine_ctx.get("verdict") or None,
        "verdict_summary": (admin_row or {}).get("verdict_summary"),
        "evidence_audit": evidence_audit,
        "ok": ok,
        "issues": issues,
        "pass": not issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask + admin audit one question")
    parser.add_argument("question", help="Question text (Hindi/English)")
    parser.add_argument("--lang", default="hi", help="hi or en")
    args = parser.parse_args()

    admin_token = _read_admin_secret()
    if not admin_token:
        print("WARN: ADMIN_SECRET not set — admin row fetch may fail", file=sys.stderr)

    print(f"API: {DEFAULT_API}")
    demo = _demo_login()
    uid = int(demo["id"])
    api_key = str(demo["api_key"])
    print(f"Demo user id={uid}")

    kundli, birth = _user_kundli(uid, api_key)
    print(f"Chart planets={len(kundli.get('planets') or [])}")

    print(f"Asking: {args.question!r}")
    ask_out = _ask_stream(args.question, args.lang, uid, api_key, kundli, birth)
    print(f"Stream done — topic={ask_out.get('topic')} source={ask_out.get('source')}")

    admin_row = None
    if admin_token:
        admin_row = _admin_latest(uid, admin_token, args.question)
        if admin_row:
            print(f"Admin row id={admin_row.get('id')}")
        else:
            print("WARN: admin row not found (check ADMIN_SECRET / deploy)", file=sys.stderr)

    report = _audit(args.question, ask_out, admin_row)
    print("\n=== ANSWER ===")
    print(report.get("answer_text") or "(empty)")
    print("\n=== PATH ===")
    print(f"source={report.get('ask_source')} | engine_tag={report.get('engine_tag')} | path={report.get('answer_path')}")
    print(f"admin_engine={report.get('admin_engine')} | archetype={report.get('admin_archetype')}")
    ev = report.get("evidence_audit") or {}
    print("\n=== CHART EVIDENCE ===")
    print(f"evidence_ok={ev.get('evidence_ok')} | locked_pick={ev.get('locked_pick')}")
    for line in ev.get("evidence_sample") or []:
        print(f"  - {line}")
    for w in ev.get("warnings") or []:
        print(f"  WARN: {w}")
    print("\n=== AUDIT ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
