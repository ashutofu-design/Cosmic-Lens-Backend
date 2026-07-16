"""Patch flask stream gates + openai_helper Phase2 routing / post-LLM."""
from __future__ import annotations

from pathlib import Path

API = Path(__file__).resolve().parents[1]


def patch_flask_stream() -> None:
    path = API / "flask_app.py"
    src = path.read_text(encoding="utf-8")
    start = "    if not question:\n        return jsonify({\"error\": \"question is required\"}), 400\n\n    try:\n        from ask_question_normalize import prepare_ask_question\n\n        question = prepare_ask_question(question)\n    except Exception:\n        pass\n\n    # Greetings / help — before language & scope gates"
    # Only the STREAM occurrence remains (ask_route already patched).
    idx = src.find("def ask_stream_route")
    if idx < 0:
        raise SystemExit("ask_stream_route missing")
    chunk = src[idx:]
    marker = "    try:\n        from ask_question_normalize import prepare_ask_question"
    m0 = chunk.find(marker)
    if m0 < 0:
        print("flask_stream: normalize already removed?")
        return
    # From normalize try through end of privacy block before RAW PASSTHROUGH comment
    abs0 = idx + m0
    end_marker = "    # ════════════════════════════════════════════════════════════════════════\n    # RAW PASSTHROUGH MODE (2026-05-06, stream parity)"
    m1 = src.find(end_marker, abs0)
    if m1 < 0:
        raise SystemExit("stream RP marker missing")
    # Keep shortcut block that sits BETWEEN normalize and language — need to reconstruct.
    # Current order: normalize → shortcut → language → scope → privacy → RP comment
    # Desired: shortcut → RP comment (no normalize/lang/scope/privacy)
    shortcut_start = src.find("    # Greetings / help — before language & scope gates", abs0)
    if shortcut_start < 0 or shortcut_start > m1:
        raise SystemExit("shortcut block not found in stream")
    shortcut_end = src.find("    try:\n        from ask_language_gate import assess_ask_language", shortcut_start)
    if shortcut_end < 0:
        raise SystemExit("language gate after shortcut not found")
    shortcut_block = src[shortcut_start:shortcut_end]
    shortcut_block = shortcut_block.replace(
        "# Greetings / help — before language & scope gates (hi/hello are not \"personal\" astro Qs).",
        "# Greetings / help only — language/scope/privacy/normalize run once inside RP.",
    )
    new_mid = (
        "\n"
        + shortcut_block
        + "    # ════════════════════════════════════════════════════════════════════════\n"
        "    # RAW PASSTHROUGH MODE (2026-05-06, stream parity) — gates owned by RP.\n"
        "    # ════════════════════════════════════════════════════════════════════════\n"
    )
    # Replace from normalize through privacy (abs0..m1) with shortcut + RP header start
    # m1 points at old RP comment — keep from m1's "try: from openai_helper" onward.
    # Find the try import after old comment
    try_imp = src.find("    try:\n        from openai_helper import raw_passthrough_ask as _rp_ask_s", m1)
    if try_imp < 0:
        raise SystemExit("rp import not found")
    new_src = src[:abs0] + new_mid + src[try_imp:]
    path.write_text(new_src, encoding="utf-8")
    print("flask_stream: deduped gates")


def patch_openai_phase2_routing() -> None:
    path = API / "openai_helper.py"
    src = path.read_text(encoding="utf-8")

    # 1) Remove refuse early-return; knowledge only on branch=knowledge
    old_refuse = '''                if _p2_branch == "refuse":
                    return _attach_admin(
                        refuse_payload(question=question or "", lang=lang or "hn"),
                        question=question or "",
                        question_type="STATIC",
                        is_timing=False,
                        llm_called=True,
                        skip_reason="understand_refuse",
                        intent_source="understand_phase2",
                        llm_intent=_llm_intent_admin,
                    )
                if _p2_branch == "knowledge":'''
    if old_refuse in src:
        src = src.replace(
            old_refuse,
            '''                if _p2_branch == "knowledge":''',
            1,
        )
        print("openai: removed refuse branch return")
    else:
        print("openai: refuse block already gone or changed")

    # Remove unused refuse_payload import usage - keep import ok if unused

    # 2) Remove emergency knowledge_fast fallback
    emerg = '''    # If Understand LLM failed, keep regex knowledge_fast as emergency only
    # (avoids Leo-gemstone soft-fail). Not the authority when Phase2 ok.
    if not _phase2_ok:
        try:
            from ask_knowledge_fast import try_astrology_knowledge_fast_answer

            _kf_fb = try_astrology_knowledge_fast_answer(
                question or "", lang=lang or "hn", force=False,
            )
            if _kf_fb:
                print(
                    f"[raw_passthrough] knowledge_fast emergency_fallback "
                    f"source={_kf_fb.get('source')!r}",
                    flush=True,
                )
                return _attach_admin(
                    _kf_fb,
                    question=question or "",
                    question_type="STATIC",
                    is_timing=False,
                    llm_called=_kf_fb.get("source") == "knowledge_fast_llm",
                    skip_reason="knowledge_fast_emergency",
                    intent_source="knowledge_fast_fallback",
                )
        except Exception as _kf_fb_exc:
            print(f"[raw_passthrough] knowledge_fast emergency skipped: {_kf_fb_exc}", flush=True)

    # Legacy paraphrase Understand'''
    if emerg in src:
        src = src.replace(
            emerg,
            '''    # Legacy paraphrase Understand''',
            1,
        )
        print("openai: removed emergency knowledge_fast")
    else:
        print("openai: emergency KF block not found")

    # 3) Skip hypothetic placement third path when Phase2 ok
    hyp = '''    try:
        from chart_fact_answer import answer_hypothetical_placement_change

        # Natal "lord ko X house me place" — fixed answer (no empty-house stub, no LLM).
        _hyp = answer_hypothetical_placement_change(question or "", lang=lang or "hn")
        if _hyp:'''
    hyp_new = '''    try:
        from chart_fact_answer import answer_hypothetical_placement_change

        # Final arch: no third path — hypothetic lock only if Phase2 unavailable.
        _hyp = None
        if not _phase2_ok:
            _hyp = answer_hypothetical_placement_change(question or "", lang=lang or "hn")
        if _hyp:'''
    if hyp in src:
        src = src.replace(hyp, hyp_new, 1)
        print("openai: gated hypothetic third path")
    else:
        print("openai: hyp block not found")

    # 4) After DNA skip / before classify — inject Phase2 sole intent authority
    needle = '''    # ── Understand meaning → route to specific static/timing engine ─────
    _llm_intent = None
    _llm_intent_record = None
    _intent_source = "regex"
'''
    inject = '''    # ── Understand meaning → route to specific static/timing engine ─────
    _llm_intent = None
    _llm_intent_record = None
    _intent_source = "regex"
    if _phase2_ok and isinstance(_phase2_understand, dict):
        try:
            from ask_understand_phase2 import phase2_llm_intent

            _llm_intent = phase2_llm_intent(
                _phase2_understand, question=question or "",
            )
            _llm_intent_record = dict(_llm_intent)
            _intent_source = "understand_phase2"
            _mr_archetype_override = _llm_intent.get("mr_archetype")
            _career_archetype_override = _llm_intent.get("career_archetype")
            _finance_archetype_override = _llm_intent.get("finance_archetype")
            _health_archetype_override = _llm_intent.get("health_archetype")
            _education_archetype_override = _llm_intent.get("education_archetype")
            _children_archetype_override = _llm_intent.get("children_archetype")
            _property_archetype_override = _llm_intent.get("property_archetype")
            _travel_archetype_override = _llm_intent.get("travel_archetype")
            _litigation_archetype_override = _llm_intent.get("litigation_archetype")
            print(
                "[raw_passthrough] PHASE2_SOLE_ROUTE "
                f"domain={_llm_intent.get('domain')} "
                f"timing={_llm_intent.get('is_timing')} "
                f"arch={_mr_archetype_override or _career_archetype_override or _health_archetype_override}",
                flush=True,
            )
        except Exception as _p2r_exc:
            print(f"[raw_passthrough] PHASE2_SOLE_ROUTE skipped: {_p2r_exc}", flush=True)

'''
    if needle in src and "PHASE2_SOLE_ROUTE" not in src:
        src = src.replace(needle, inject, 1)
        print("openai: injected PHASE2_SOLE_ROUTE")
    else:
        print("openai: sole route inject skipped")

    # 5) Skip classify_and_route when phase2 already set intent
    old_cls = '''    if (os.environ.get("ASK_LLM_INTENT") or "1").strip() == "1":
        try:
            from ask_route_from_understanding import classify_and_route_ask

            _route = classify_and_route_ask('''
    new_cls = '''    if (not _phase2_ok) and (os.environ.get("ASK_LLM_INTENT") or "1").strip() == "1":
        try:
            from ask_route_from_understanding import classify_and_route_ask

            _route = classify_and_route_ask('''
    if old_cls in src:
        src = src.replace(old_cls, new_cls, 1)
        print("openai: skip classify when phase2")
    else:
        print("openai: classify gate not found")

    # 6) After static flag init, apply phase2 flags and skip detectors
    flag_init = '''    _is_mr_static = False
    _is_career_static = False
    _is_finance_static = False
    _is_health_static = False
    _is_education_static = False
    _is_children_static = False
    _is_property_static = False
    _is_vehicle_static = False
    _is_numerology_static = False
    _is_travel_static = False
    _is_litigation_static = False
    _is_luck_static = False
    _is_network_static = False
    _is_gap_static = False
    _gap_static_key = ""
    _direct_llm_bypass = False
    _direct_llm_reason = ""
    try:
        from ask_routing_policy import should_bypass_static_engines_for_direct_llm

        _direct_llm_bypass, _direct_llm_reason = should_bypass_static_engines_for_direct_llm(
'''
    flag_inject = '''    _is_mr_static = False
    _is_career_static = False
    _is_finance_static = False
    _is_health_static = False
    _is_education_static = False
    _is_children_static = False
    _is_property_static = False
    _is_vehicle_static = False
    _is_numerology_static = False
    _is_travel_static = False
    _is_litigation_static = False
    _is_luck_static = False
    _is_network_static = False
    _is_gap_static = False
    _gap_static_key = ""
    _direct_llm_bypass = False
    _direct_llm_reason = ""
    _phase2_flags_applied = False
    if _phase2_ok and isinstance(_phase2_understand, dict) and str(_phase2_understand.get("branch") or "engine") == "engine":
        try:
            from ask_understand_phase2 import phase2_engine_static_flags

            _pf = phase2_engine_static_flags(_phase2_understand)
            _is_education_static = bool(_pf.get("education"))
            _is_children_static = bool(_pf.get("children"))
            _is_property_static = bool(_pf.get("property"))
            _is_vehicle_static = bool(_pf.get("vehicle"))
            _is_travel_static = bool(_pf.get("travel"))
            _is_litigation_static = bool(_pf.get("litigation"))
            _is_gap_static = bool(_pf.get("gap"))
            _is_network_static = bool(_pf.get("network"))
            _is_luck_static = bool(_pf.get("luck"))
            _is_career_static = bool(_pf.get("career"))
            _is_finance_static = bool(_pf.get("finance"))
            _is_health_static = bool(_pf.get("health"))
            _is_mr_static = bool(_pf.get("mr"))
            _direct_llm_bypass = False
            _direct_llm_reason = ""
            _phase2_flags_applied = True
            is_timing = bool(_phase2_understand.get("timing"))
            qtype = "TIMING" if is_timing else "STATIC"
            print(
                f"[raw_passthrough] PHASE2_ENGINE_FLAGS "
                f"mr={_is_mr_static} career={_is_career_static} health={_is_health_static} "
                f"finance={_is_finance_static} timing={is_timing}",
                flush=True,
            )
        except Exception as _p2f_exc:
            print(f"[raw_passthrough] PHASE2_ENGINE_FLAGS skipped: {_p2f_exc}", flush=True)
    if not _phase2_flags_applied:
      try:
        from ask_routing_policy import should_bypass_static_engines_for_direct_llm

        _direct_llm_bypass, _direct_llm_reason = should_bypass_static_engines_for_direct_llm(
'''
    # This indentation change is risky - wrapping the whole detector block in `if not _phase2_flags_applied`
    # is huge. Simpler: apply phase2 flags AFTER all detectors overwrite them.
    # Instead of wrapping, re-apply phase2 flags just before engine resolver.

    # Simpler approach: force bypass false always + re-apply phase2 flags before resolver
    if "PHASE2_ENGINE_FLAGS" not in src:
        # Just force bypass off after the early bypass call
        bypass_call = '''        _direct_llm_bypass, _direct_llm_reason = should_bypass_static_engines_for_direct_llm(
            question or "",
            _llm_intent if isinstance(_llm_intent, dict) else (
                _llm_intent_admin if isinstance(_llm_intent_admin, dict) else None
            ),
        )
    except Exception:
        pass'''
        bypass_force = '''        _direct_llm_bypass, _direct_llm_reason = should_bypass_static_engines_for_direct_llm(
            question or "",
            _llm_intent if isinstance(_llm_intent, dict) else (
                _llm_intent_admin if isinstance(_llm_intent_admin, dict) else None
            ),
        )
    except Exception:
        pass
    # Final arch: never bypass engines for prediction path.
    _direct_llm_bypass = False
    _direct_llm_reason = ""'''
        if bypass_call in src:
            src = src.replace(bypass_call, bypass_force, 1)
            print("openai: forced bypass false after early call")
        else:
            print("openai: early bypass call pattern not found")

        # Re-apply phase2 flags immediately before engine resolver
        resolver = '''    _engine_route = None
    if not is_timing and not _is_native_overview:
        try:
            from ask_engine_resolver import (
                merge_route_into_admin_intent,
                resolve_static_engine_route,
            )'''
        resolver_pre = '''    # Phase2 Understand is sole routing authority for engine selection.
    if _phase2_ok and isinstance(_phase2_understand, dict) and str(_phase2_understand.get("branch") or "engine") == "engine":
        try:
            from ask_understand_phase2 import phase2_engine_static_flags

            _pf = phase2_engine_static_flags(_phase2_understand)
            _is_education_static = bool(_pf.get("education"))
            _is_children_static = bool(_pf.get("children"))
            _is_property_static = bool(_pf.get("property"))
            _is_vehicle_static = bool(_pf.get("vehicle"))
            _is_travel_static = bool(_pf.get("travel"))
            _is_litigation_static = bool(_pf.get("litigation"))
            _is_gap_static = bool(_pf.get("gap"))
            _is_network_static = bool(_pf.get("network"))
            _is_luck_static = bool(_pf.get("luck"))
            _is_career_static = bool(_pf.get("career"))
            _is_finance_static = bool(_pf.get("finance"))
            _is_health_static = bool(_pf.get("health"))
            _is_mr_static = bool(_pf.get("mr"))
            _direct_llm_bypass = False
            _direct_llm_reason = ""
            is_timing = bool(_phase2_understand.get("timing"))
            qtype = "TIMING" if is_timing else "STATIC"
            print(
                f"[raw_passthrough] PHASE2_ENGINE_FLAGS "
                f"mr={_is_mr_static} career={_is_career_static} health={_is_health_static} "
                f"finance={_is_finance_static} timing={is_timing}",
                flush=True,
            )
        except Exception as _p2f_exc:
            print(f"[raw_passthrough] PHASE2_ENGINE_FLAGS skipped: {_p2f_exc}", flush=True)

    _engine_route = None
    if not is_timing and not _is_native_overview:
        try:
            from ask_engine_resolver import (
                merge_route_into_admin_intent,
                resolve_static_engine_route,
            )'''
        if resolver in src:
            src = src.replace(resolver, resolver_pre, 1)
            print("openai: PHASE2_ENGINE_FLAGS before resolver")
        else:
            print("openai: resolver marker not found")
    else:
        print("openai: PHASE2_ENGINE_FLAGS already present")

    # 7) Disable open_chart third path on MR verify when phase2
    oca = '''                        if not _mr_ver.ok and _mr_ver.action == "d1_open_chart":
                            from ask_chart_open_qa import (
                                open_chart_qa_slice_meta,
                                run_open_chart_qa,
                            )

                            _oca_rec = run_open_chart_qa('''
    oca_new = '''                        if (not _phase2_ok) and (not _mr_ver.ok) and _mr_ver.action == "d1_open_chart":
                            from ask_chart_open_qa import (
                                open_chart_qa_slice_meta,
                                run_open_chart_qa,
                            )

                            _oca_rec = run_open_chart_qa('''
    if oca in src:
        src = src.replace(oca, oca_new, 1)
        print("openai: disabled open_chart when phase2")
    else:
        print("openai: open_chart block not found")

    path.write_text(src, encoding="utf-8")
    print("openai_helper routing patches written")


def main() -> None:
    patch_flask_stream()
    patch_openai_phase2_routing()
    # post-llm strip
    import runpy
    runpy.run_path(str(API / "scripts" / "_arch_debt_strip_post_llm.py"), run_name="__main__")


if __name__ == "__main__":
    main()
