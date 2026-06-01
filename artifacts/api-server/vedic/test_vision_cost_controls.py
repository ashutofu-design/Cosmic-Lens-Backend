"""Cheap preview + negative cache + preview rate limit."""
import os

import vision_layer as vl


def test_negative_cache_blocks_repeat_bad_upload(monkeypatch):
    monkeypatch.setenv("ASTROVASTU_VISION_CACHE_DISABLE", "1")
    payload = {"type": "image", "base64": "aGVsbG8=", "north_at": "top"}

    vl._negative_cache_put("testfp", "not a plan", "invalid_floor_plan")
    monkeypatch.setattr(vl, "_upload_fingerprint", lambda *a, **k: "testfp")

    vd, err, code = vl.extract_floor_plan_from_upload(
        payload, preview_mode=True,
    )
    assert vd == {}
    assert err == "not a plan"
    assert code == "invalid_floor_plan"


def test_preview_retries_high_when_first_pass_empty(monkeypatch):
    monkeypatch.setenv("ASTROVASTU_VISION_CACHE_DISABLE", "1")
    monkeypatch.setenv("ASTROVASTU_PREVIEW_RETRY_HIGH", "1")
    payload = {"type": "image", "base64": "aGVsbG8=", "north_at": "top"}
    monkeypatch.setattr(vl, "_upload_fingerprint", lambda *a, **k: "retryfp")
    vl._negative_cache_clear("retryfp")

    calls: list[str] = []

    def fake_extract(_url, **kw):
        calls.append(kw.get("vision_detail") or "")
        if len(calls) == 1:
            return {
                "scan_inconclusive": True,
                "rooms": [],
                "confidence": 25,
                "inconclusive_reason": "too small",
            }
        return {
            "scan_inconclusive": False,
            "confidence": 82,
            "rooms": [
                {"room_type": "kitchen", "direction": "SE"},
                {"room_type": "bedroom", "direction": "SW"},
            ],
        }

    monkeypatch.setattr(vl, "_preview_vision_detail", lambda: "low")
    monkeypatch.setattr(
        "openai_helper.extract_floor_plan_layout",
        fake_extract,
    )
    monkeypatch.setattr(
        "floor_plan_loader.to_image_data_url",
        lambda *a, **k: "data:image/png;base64,AA==",
    )

    vd, err, code = vl.extract_floor_plan_from_upload(payload, preview_mode=True)
    assert err is None
    assert code is None
    assert len(vd.get("rooms") or []) >= 2
    assert len(calls) == 2
    assert calls[1] == "high"


def test_finalize_drops_duplicate_stores():
    from vision_layer import _finalize_engine_rooms

    er = [
        {"room_type": "store", "direction": "NW"},
        {"room_type": "store", "direction": "NE"},
        {"room_type": "kitchen", "direction": "SE"},
    ]
    fr = [{"room_type": r["room_type"], "direction": r["direction"], "position_grid": "", "notes": ""} for r in er]
    out_er, _ = _finalize_engine_rooms(er, fr, {"main_entrance_direction": "S"})
    assert not any(r["room_type"] == "store" for r in out_er)
    assert any(r["room_type"] == "kitchen" for r in out_er)


def test_inject_main_door_from_entrance():
    from vision_layer import _finalize_engine_rooms

    er = [{"room_type": "kitchen", "direction": "SE"}]
    fr = [{"room_type": "kitchen", "direction": "SE", "position_grid": "", "notes": ""}]
    out_er, _ = _finalize_engine_rooms(er, fr, {"main_entrance_direction": "S"})
    assert any(r["room_type"] == "main_door" and r["direction"] == "S" for r in out_er)


def test_preview_rate_limit():
    uid = 999001
    vl._PREVIEW_RATE.pop(str(uid), None)
    for _ in range(12):
        ok, _ = vl.check_floor_plan_preview_rate(uid, lang="en")
        assert ok
    ok, msg = vl.check_floor_plan_preview_rate(uid, lang="en")
    assert not ok
    assert "hour" in msg.lower() or "wait" in msg.lower()
