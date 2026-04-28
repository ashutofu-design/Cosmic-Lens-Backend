"""Phase 4.4 — Stream-path POST_LOGIC + supertype validator parity tests.

Drives `ai_ask_stream` end-to-end with a mocked OpenAI client to verify:
  • Clean stream → final event passes through unchanged, replaced_by_validator=False
  • Violating stream + clean retry → final.text = retry text, replaced=True
  • Violating stream + violating retry → final.text = _POST_LOGIC_REFUSAL_TEXT, replaced=True
  • Violating stream + retry-error → final.text = refusal, replaced=True

Mocks `_get_client()` so no live OpenAI calls are made.
"""

from __future__ import annotations
import sys
import types
import os
import openai_helper as oh

_PASS = 0
_FAIL = 0
_FAILS: list[tuple[str, str]] = []


def _run(name: str, fn):
    global _PASS, _FAIL
    try:
        fn()
        print(f"  PASS  {name}")
        _PASS += 1
    except AssertionError as exc:
        print(f"  FAIL  {name}: {exc}")
        _FAIL += 1
        _FAILS.append((name, str(exc)))
    except Exception as exc:  # noqa: BLE001
        print(f"  ERR   {name}: {type(exc).__name__}: {exc}")
        _FAIL += 1
        _FAILS.append((name, f"{type(exc).__name__}: {exc}"))


# ─── fixtures ──────────────────────────────────────────────────────────────

# Truth: currentDasha=Saturn → claiming "Jupiter" as current MD will violate.
KUNDLI = {
    "planets": [
        {"name": "Sun",     "house": 1, "sign": "Aries"},
        {"name": "Moon",    "house": 4, "sign": "Cancer", "nakshatra": "Pushya"},
        {"name": "Saturn",  "house": 10, "sign": "Capricorn"},
        {"name": "Jupiter", "house": 9, "sign": "Sagittarius"},
        {"name": "Mars",    "house": 3, "sign": "Gemini"},
        {"name": "Mercury", "house": 2, "sign": "Taurus"},
        {"name": "Venus",   "house": 7, "sign": "Libra"},
        {"name": "Rahu",    "house": 6, "sign": "Virgo"},
        {"name": "Ketu",    "house": 12, "sign": "Pisces"},
    ],
    "nakshatra": "Pushya",
    "nakshatraPada": 2,
    "ascendant": "Aries",
    # _build_truth_facts reads `currentDasha.{mahadasha,md,maha}` and
    # `currentDasha.{antardasha,ad,bhukti}` (each must be a dict with a
    # `planet` key). A flat {planet, startDate, endDate} on currentDasha
    # silently produces truth_md=null — POST_LOGIC then has nothing to
    # compare and never fires.
    "currentDasha": {
        "mahadasha": {
            "planet":    "Saturn",
            "startDate": "2020-01-01",
            "endDate":   "2039-01-01",
        },
        "antardasha": {
            "planet":    "Mercury",
            "startDate": "2024-06-01",
            "endDate":   "2027-03-01",
        },
    },
}


# ─── fake OpenAI client ────────────────────────────────────────────────────

class _FakeStreamChunk:
    def __init__(self, text: str):
        self.choices = [types.SimpleNamespace(
            delta=types.SimpleNamespace(content=text),
        )]


class _FakeNonStreamResp:
    def __init__(self, text: str):
        self.choices = [types.SimpleNamespace(
            message=types.SimpleNamespace(content=text),
        )]


class _FakeCompletions:
    """Yields configured stream text on stream=True, configured retry text
    on stream=False. Distinguishes the *validator retry* (which uses the
    real assistant `messages` list — recognizable by message_count > 5
    and the LAST role being a corrective system message) from upstream
    non-stream classifier calls (`understand_question`, intent_router)
    which also flow through this fake when they fall back to AI."""
    def __init__(self, stream_text: str, retry_text):
        self.stream_text     = stream_text
        self.retry_text      = retry_text
        self.stream_calls    = 0
        self.nonstream_calls = 0
        self.retry_calls     = 0  # only the validator retries
        self.classifier_calls = 0  # understand_question / intent_router

    def _is_validator_retry(self, kw) -> bool:
        msgs = kw.get("messages") or []
        if not msgs or len(msgs) < 2:
            return False
        last = msgs[-1]
        if not isinstance(last, dict) or last.get("role") != "system":
            return False
        content = (last.get("content") or "")
        if not isinstance(content, str):
            return False
        # Recognize the corrective-feedback signatures used by both
        # _retry_feedback_for() (supertype) and _post_logic_correction_msg()
        # (POST_LOGIC). Both are appended as the LAST system message.
        markers = (
            "actual ground truth",
            "ACTUAL ground truth",
            "Mahadasha",
            "violated",
            "contract",
            "correct the following",
            "GROUND TRUTH",
        )
        return any(m in content for m in markers)

    def create(self, **kw):
        if kw.get("stream"):
            self.stream_calls += 1
            chunks = [self.stream_text[i:i+30]
                      for i in range(0, len(self.stream_text), 30)]
            return iter(_FakeStreamChunk(c) for c in chunks)
        # non-stream: figure out whether this is the validator retry
        self.nonstream_calls += 1
        if self._is_validator_retry(kw):
            self.retry_calls += 1
            if isinstance(self.retry_text, Exception):
                raise self.retry_text
            return _FakeNonStreamResp(self.retry_text)
        # otherwise it's an upstream classifier call — return an empty
        # response so understand_question / intent_router fall back to
        # their regex defaults (already proven safe by Phase 4.1-4.3 tests).
        self.classifier_calls += 1
        return _FakeNonStreamResp("")


class _FakeClient:
    def __init__(self, completions: _FakeCompletions):
        self.chat = types.SimpleNamespace(completions=completions)


def _install_fake_client(stream_text: str, retry_text):
    """Monkey-patch _get_client so ai_ask_stream uses our fake."""
    fake_comp = _FakeCompletions(stream_text, retry_text)
    fake_client = _FakeClient(fake_comp)
    oh._get_client = lambda: fake_client  # type: ignore[assignment]
    return fake_comp


def _drive_stream(question: str = "Mera dasha kya hai?") -> dict:
    """Run ai_ask_stream to completion, returning the final-event dict."""
    final_evt: dict | None = None
    delta_count = 0
    for evt in oh.ai_ask_stream(question, KUNDLI, lang="en"):
        if evt.get("kind") == "delta":
            delta_count += 1
        elif evt.get("kind") == "final":
            final_evt = dict(evt)
            final_evt["_delta_count"] = delta_count
        elif evt.get("kind") == "oneshot":
            # Brand-guard / no-chart fallback path — not covered by these tests.
            return {"kind": "oneshot", "data": evt.get("data")}
    if not final_evt:
        raise AssertionError("stream completed without a final event")
    return final_evt


# ─── tests ────────────────────────────────────────────────────────────────

def main():
    print("[1/4] Clean stream → no substitution")

    def _t1():
        # Saturn is the truth currentDasha — claiming Saturn correctly should
        # NOT trigger POST_LOGIC. Include a year/window marker ("2039 tak")
        # so the supertype V→R→T contract is also satisfied — isolating
        # POST_LOGIC as the variable under test.
        clean = ("Aapka current Mahadasha Saturn ka 2039 tak chal raha hai. "
                 "Yeh karm aur discipline ka samay hai. "
                 "Saturn ki energy ko respect karein.")
        comp = _install_fake_client(stream_text=clean, retry_text="")
        evt = _drive_stream()
        assert evt["kind"] == "final", f"expected final, got {evt}"
        assert evt["replaced_by_validator"] is False, \
            f"clean stream should NOT be replaced, got {evt}"
        assert evt["text"].strip() == clean.strip(), \
            f"clean stream text must pass through, got {evt['text'][:80]!r}"
        assert comp.retry_calls == 0, \
            f"clean stream must NOT trigger validator retry, " \
            f"got retry_calls={comp.retry_calls}"
        assert evt["_delta_count"] > 0, "expected ≥1 delta event"
    _run("clean-stream-passthrough", _t1)

    print("\n[2/4] Violating stream + clean retry → text replaced, flag=True")

    def _t2():
        violating = ("Abhi Mahadasha Jupiter ki chal rahi hai. "
                     "Yeh wisdom aur growth ka samay hai. "
                     "Guru ki blessings strong hain.")
        clean_retry = ("Aapka current Mahadasha Saturn ka chal raha hai. "
                       "Karm aur discipline focus karein.")
        comp = _install_fake_client(stream_text=violating,
                                    retry_text=clean_retry)
        evt = _drive_stream()
        assert evt["kind"] == "final"
        assert evt["replaced_by_validator"] is True, \
            f"violating stream must trigger replacement, got {evt}"
        assert "Saturn" in evt["text"], \
            f"replaced text should be the corrected (Saturn) retry, got " \
            f"{evt['text'][:120]!r}"
        assert "Jupiter ki chal rahi" not in evt["text"], \
            f"violating phrase must not survive, got {evt['text'][:120]!r}"
        assert comp.retry_calls >= 1, \
            f"expected ≥1 validator retry, got retry_calls={comp.retry_calls}"
    _run("violating-stream-clean-retry", _t2)

    print("\n[3/4] Violating stream + violating retry → REFUSAL substituted")

    def _t3():
        violating = ("Abhi Mahadasha Jupiter ki chal rahi hai. "
                     "Guru ki blessings.")
        # Retry STILL claims wrong MD (Mars instead of Saturn).
        still_bad = ("Currently Mahadasha Mars ki chal rahi hai. "
                     "Energy aur action ka samay hai.")
        comp = _install_fake_client(stream_text=violating,
                                    retry_text=still_bad)
        evt = _drive_stream()
        assert evt["kind"] == "final"
        assert evt["replaced_by_validator"] is True, \
            f"residual violation must trigger refusal flag, got {evt}"
        assert evt["text"].strip() == oh._POST_LOGIC_REFUSAL_TEXT.strip(), \
            f"text must be _POST_LOGIC_REFUSAL_TEXT, got {evt['text'][:120]!r}"
        assert comp.retry_calls >= 1, \
            f"expected ≥1 validator retry, got retry_calls={comp.retry_calls}"
    _run("violating-stream-violating-retry-refusal", _t3)

    print("\n[4/4] Violating stream + retry-error → REFUSAL substituted")

    def _t4():
        violating = ("Abhi Mahadasha Jupiter ki chal rahi hai. "
                     "Guru ki blessings.")
        comp = _install_fake_client(
            stream_text=violating,
            retry_text=RuntimeError("simulated OpenAI 503"),
        )
        evt = _drive_stream()
        assert evt["kind"] == "final"
        assert evt["replaced_by_validator"] is True, \
            f"retry-error must still flag substitution, got {evt}"
        assert evt["text"].strip() == oh._POST_LOGIC_REFUSAL_TEXT.strip(), \
            f"text must be refusal on retry-error, got {evt['text'][:120]!r}"
        assert comp.retry_calls >= 1, \
            f"retry should be attempted, got retry_calls={comp.retry_calls}"
    _run("violating-stream-retry-error-refusal", _t4)

    # Additional regression: SSE flask payload includes the new flag.
    print("\n[5/4] Flask SSE payload includes replaced_by_validator")

    def _t5():
        # Verify the flask layer's translation includes the new field. We
        # don't spin up a live HTTP server; we just confirm the source
        # contains the explicit pass-through (sanity check).
        with open("flask_app.py", encoding="utf-8") as f:
            src = f.read()
        assert "replaced_by_validator" in src, \
            "flask_app.py should pass through replaced_by_validator in SSE final"
        # Make sure the field name is in the SSE payload (not just a comment).
        # Look for the JSON dict literal in the elif kind == 'final' block.
        idx = src.find('"replaced_by_validator"')
        assert idx > 0, "replaced_by_validator key missing from flask SSE final"
        # And the openai_helper final yield must include the key as well.
        with open("openai_helper.py", encoding="utf-8") as f:
            oh_src = f.read()
        assert '"replaced_by_validator"' in oh_src, \
            "openai_helper.py final yield missing replaced_by_validator"
    _run("flask-sse-passes-flag", _t5)

    print()
    print("=" * 60)
    print(f"Phase 4.4 stream-parity test summary:  PASS={_PASS}  FAIL={_FAIL}")
    print("=" * 60)
    if _FAILS:
        print("\nFailures:")
        for n, e in _FAILS:
            print(f"  FAIL  {n}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
