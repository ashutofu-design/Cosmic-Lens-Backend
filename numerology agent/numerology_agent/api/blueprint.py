"""Flask blueprint for the Numerology Agent.

Prefix ``/api/numerology-agent`` does not collide with ``/api/numerology/pdf``.
Mounted on Cosmic Lens ``flask_app.py`` via ``numerology_agent_bridge``.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from numerology_agent.agent.orchestrator import NumerologyAgent
from numerology_agent.api.jobs import get_job, start_report_job
from numerology_agent.exceptions import NumerologyAgentError
from numerology_agent.logging_setup import get_logger

log = get_logger("api")

numerology_agent_bp = Blueprint(
    "numerology_agent",
    __name__,
    url_prefix="/api/numerology-agent",
)

_agent: NumerologyAgent | None = None


def get_agent() -> NumerologyAgent:
    global _agent
    if _agent is None:
        _agent = NumerologyAgent()
    return _agent


def _with_caller_credentials(body: dict) -> dict:
    """Lift the caller's Cosmic Lens credentials out of headers into extras.

    ``attach_saved_d1`` needs the user's api_key to fetch their stored chart.
    Headers keep the key out of the request body so it cannot leak through
    body-logging middleware or proxy buffers. The body form is still honoured
    for older clients. Report jobs run on a worker thread with no request
    context, so this must happen before the job is queued.
    """
    api_key = (request.headers.get("X-API-Key") or "").strip()
    user_id = (request.headers.get("X-User-Id") or "").strip()
    if not api_key and not user_id:
        return body
    merged = dict(body)
    if api_key and not str(merged.get("api_key") or "").strip():
        merged["api_key"] = api_key
    if user_id and not str(merged.get("user_id") or "").strip():
        merged["user_id"] = user_id
    return merged


@numerology_agent_bp.route("/health", methods=["GET"])
def health():
    result = get_agent().run({"intent": "health", "name": "health", "dob": "1970-01-01"})
    return jsonify(
        {
            "ok": True,
            "service": "numerology_agent",
            "status": "ok",
            "tools": result.get("tools") or [],
            "specialists": result.get("specialists") or [],
        }
    )


@numerology_agent_bp.route("/run", methods=["POST"])
def run():
    body = request.get_json(silent=True) or {}
    try:
        result = get_agent().run(body)
    except NumerologyAgentError as exc:
        return jsonify(exc.to_dict()), exc.http_status
    return jsonify(result), 200


@numerology_agent_bp.route("/report/plan", methods=["POST"])
def report_plan():
    body = request.get_json(silent=True) or {}
    try:
        result = get_agent().plan_report(body)
    except NumerologyAgentError as exc:
        return jsonify(exc.to_dict()), exc.http_status
    return jsonify(result), 200


@numerology_agent_bp.route("/report/generate", methods=["POST"])
def report_generate():
    body = _with_caller_credentials(request.get_json(silent=True) or {})
    try:
        result = get_agent().generate_report(body)
    except NumerologyAgentError as exc:
        return jsonify(exc.to_dict()), exc.http_status
    return jsonify(result), 200


@numerology_agent_bp.route("/report/generate/start", methods=["POST"])
def report_generate_start():
    body = _with_caller_credentials(request.get_json(silent=True) or {})
    job_id = start_report_job(body, get_agent().generate_report)
    return jsonify({"ok": True, "job_id": job_id, "percent": 1, "stage": "queued"}), 202


@numerology_agent_bp.route("/report/generate/status/<job_id>", methods=["GET"])
def report_generate_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "not_found", "message": "job not found"}), 404
    return jsonify(job), 200


@numerology_agent_bp.route("/tools", methods=["GET"])
def list_tools():
    return jsonify({"ok": True, "tools": list(get_agent().tools.names())})
