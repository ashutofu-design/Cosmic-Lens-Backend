# Cosmic Lens — Engine Lineage & Phase History

Reference for the 5 timing engines, shared helpers, companion modules, the
UNIVERSAL TIMING RULE, and the consolidated phase history. Trimmed out of
`replit.md` to keep that file lean.

## UNIVERSAL TIMING RULE (Phase 2.5.11.15, MANDATORY for ALL engines)

For ANY event-prediction question — past, present, OR future
("kab hoga / kab gaya tha / kab jaaunga / when") — Jupiter+Saturn
DOUBLE TRANSIT (K.N.Rao classical rule) is COMPULSORY on the
**concerned house AND concerned house lords**. Dasha alone is never
sufficient.

- Helper: `event_timing/_shared/double_transit.py::check_double_transit(...)`
- Concern-house presets (single source of truth):
  - `travel  = [3, 9, 12]`
  - `health  = [1, 6, 8, 12]`
  - `finance = [2, 5, 9, 11]`
  - `marriage= [7, 2, 8, 11]`
  - `baby    = [5, 11]`
  - `career  = [10, 6, 2, 11]`
- Every timing engine MUST annotate `past_windows / current_window /
  next_windows` with a `double_transit` field AND append the
  `DOUBLE_TRANSIT_TIMING_RULE_APPLIED` directive.
- **Caveat**: empirically failed on travel ground-truth (Phase
  2.5.11.15-c) — rule is RETAINED but framework re-design pending
  before health/finance/marriage rollout.

## Engine Lineage (Phases 2.2 → 2.5.11)

Five timing engines (Health v1, Marriage v2.4, Finance v1, Travel v1,
Baby v1) all follow the same pipeline (FILTER → VERIFY → KP-GATE →
ACTIVATE → TRIGGER): D1 lean filter → D9 dignity → divisional chart
(D7 babies / D2 finance / D4 travel) → KP CSL of topic cusps →
weighted ranking → dasha activation (AD=5, PD=6, MD=1) →
transits/yogas. Each engine emits a `▸ <TOPIC>` row to
`locked_facts.py` + mandatory `llm_directives` + thread-local cache.
Every engine has a paired `test_<topic>_engine.py`.

### Per-engine specifics

- **Health v1** (post-2.5.11.11): 6-step (D30 + transits + SAV all
  permanently removed). Weights D1·40 + D9·30 + KP·20 + karaka·10. KP
  CSL of 6/8/12 cusps + active-CSL gate + dusthana convergence in
  `at_risk_planets` ranking.
- **Finance v1** (post-2.5.11.12-b): 5-step (D2 Hora + transits + SAV
  + Yogas removed). KP CSL of 2/5/9/11 acts as **hard final-filter**
  with safe fallback. Weights D1·40 + D9·30 + KP·20 + karaka·10.
- **Travel v1**: full 8-step. KP-dasha gate (NL→SB→SS chain hits on
  3/9/12) boosts MD/AD/PD windows independently of D1 ranking.
  Past-window lookback (15y, MD-diversity cap of 4 in top 12).
- **Marriage v2.4**: multi-format DOB parsing + practical-age floor
  for marriage windows + specific-partner synastry bridge.
- **Baby v1** (2.5.0→2.5.10): cross-chart filter (D1∩D9∩D7), KP
  2-5-11 significator gate, K.N.Rao Double Transit, gestation-aware
  re-rank, mandatory `NO_GENDER_PREDICTION` directive (PCPNDT
  compliance).

### Shared helpers (`event_timing/_shared/`)

- **`kp_significator_scan.py`**:
  `compute_kp_planet_scan(kp, domain, in_filter_set)` — scans all 9
  vimshottari planets across 6 domains via `CONCERN_HOUSES` preset,
  returns layered houses + `delivers ∈ {STRONG,PARTIAL,ABSENT}` +
  audit-flag for engine-dropped-but-delivers planets.
  `kp_promote_survivors(d1_map, kp, domain, threshold=2)` —
  data-adaptive STEP1 promotion (mutates `d1_map` to set
  `in_filter=True` for any planet whose KP chain signifies ≥threshold
  domain houses; engine's hardcoded floor retained as safety net).
- **`double_transit.py`**:
  `check_double_transit(kundli, target_date, lagna_si, planets_d1,
  concern_houses)` — K.N.Rao Jupiter+Saturn classical rule. Returns
  `{verdict, score 0-100, anchors[]}`. Vedic full-strength aspects
  (J: 5/7/9; S: 3/7/10) checked vs concern-house signs AND concern
  house-lords' natal signs.

### Companion modules

- **Remedy Engine v1.1**: hybrid 3-tier (PRACTICAL → AYURVEDIC →
  VEDIC last) covering health/marriage/career/money/business × 9
  grahas; anti-superstition rules, every entry carries KPI + cost +
  caveats.
- **Dasha Timeline Block**: `_format_dasha_block` emits current
  MD/AD/PD + every dasha transition over next 5 years; handles both
  `{planet,startDate,subDashas}` and `{lord,start,antardashas}`
  shapes; hard-cap 60 lines.
- **Ask-flow Sensitivity** (Phases 2.5.11.4-.6): `_SENSITIVE_STATIC_RE`
  covers parent-illness/anxiety/panic/suicidal/depression/addiction/
  job-loss; `_LONG_STORY_RE` for "N saal se" pattern;
  `_MARRIAGE_DOMAIN_RE` with 6 framing protocols;
  `_SPECIFIC_PARTNER_RE` routes "mere BF/wife/pati" Qs to real
  synastry (when partner kundli saved) or `requires_partner_profile`
  CTA.

## Phase History (consolidated)

### Phase 2.5.11.23 — Kundli Milan Pro PDF (May 8 2026)
Premium 24-page "Cosmic Relationship Blueprint Pro". 5 new modules
under `vedic/compat/`: `d9_marriage.py` (D9 lagna/7H/Venus/7L per
partner + cross-sync `score_0_10`), `synastry_7l.py` (each partner's
7L planet placed in OTHER's D1 + Venus/Jupiter overlays + nakshatra
resonance), `kp_marriage_promise.py` (7th-cusp sub-lord significator
chain → `verdict ∈ {STRONG,PARTIAL,WEAK,UNAVAILABLE}`),
`chapter_scores.py` (deterministic 7-chapter scores 0-10, **never
LLM**), `premium_chapters.py` (`polish_premium_chapters()` calls
`gpt-4o`, gated by `COMPAT_PREMIUM_POLISH=1`, two-tier cache, always-
safe fallback). `milan_pdf.py` extended with `render_milan_pro_pdf()`
— fixed 24-page A4 skeleton (P1 cover, P2 snapshot, P3 hidden-truth,
P4-17 seven chapters × 2pp, P18 special, P19 damage, P20 practical,
P21 koot-decoded, P22 timing-sync, P23 verdict, P24 closing). New
endpoint `POST /api/kundli-milan/pro-pdf` accepts BOTH
`{p1, p2, lang}` (mobile-friendly, server computes everything) and
`{milan, kundli_p1, kundli_p2, lang}` (advanced). **Architect-fixed
in same patch**: chapter-key contract drift (renderer index-fallback
`ch1..ch7`), jargon leak in `_kp_signature_line` (plain-language band
map), endpoint error leakage (no detail in 500), `_ch7_future`
numeric coercion+clamp. **Mobile**:
`app/kundli-milan.tsx::handleDownloadProPdf` now single-call to
`/api/kundli-milan/pro-pdf` with `{p1, p2, lang}`. 63 unit tests
green. 3-lang live smoke green.

### Phase 2.5.11.22 — My Reports Local PDF Registry (May 8 2026)
New `lib/localReports.ts` (AsyncStorage `cosmic.localReports.v1` +
`documentDirectory/reports/`): `saveLocalReport`, `listLocalReports`,
`deleteLocalReport`, `shareLocalReport`, `openLocalReport`. Wired
into every PDF download path. `app/my-reports.tsx` extended with
"Saved on this device" section. `app/(tabs)/profile.tsx` MY DATA
gains "AstroVastu Pro" + "My Reports" rows. **Architect-fixed**:
broken-entry leak (`getInfoAsync` verify), AsyncStorage race
condition (`withWriteLock` mutex), my-reports error-state hides
local items (slim red banner instead of blank screen), disk-bloat
orphan files (best-effort delete cache copies + self-heal pruning).

### Phase 2.5.11.21-C — Kundli Milan PDF 12-Page Premium Redesign (May 8 2026)
`milan_pdf.py` rewritten to fixed 12-page A4 skeleton (P1 cover, P2
snapshot, P3-P8 six deep chapters, P9 special, P10 damage, P11
practical, P12 final). New helpers: `_canon_koot_key` (alias map
`vasya→vashya`, `maitri→graha`, `bhakut→bhakoot`), `_is_manglik`
(single source of truth), `_KOOT_STRENGTH_LANG`/`_DAMAGE_LANG`
maps, derive bullets from existing payload (zero new LLM cost).
**Architect-fixed**: variable page-count drift (always 12),
real-payload koot key mismatch, manglik check inconsistency.

### Earlier consolidated (Phases 2.5.11.4 → 2.5.11.21-B)
Ask-flow sensitivity + marriage psychology + specific-partner
synastry bridge (.4-.6); Health/Finance KP convergence waves
(.9-.12-b — Health D30 removal, KP 3-layer at-risk, Finance KP-as-
final-filter); Travel past-window lookback + architect follow-up
(.14, .14-b); Universal Double-Transit K.N.Rao shared helper (.15,
.15-c — empirically failed on travel, kept as universal mandate);
Travel Moon-floor + KP-Dasha-Gate + diversification (.16);
KP-Driven STEP1 Auto-Promote `kp_promote_survivors` across all 5
engines (.18); Ask Q&A persistence on raw passthrough sync+stream
exits with `answer_text/answer_source` (.19); Kundli Milan LLM
Prose Polish HYBRID layer with gpt-4o-mini + 7-rule validator + LRU
cache (.20); persistent two-tier DB cache `KundliMilanCache` +
token trim (.20-A); validator multi-word nakshatra fix + dynamic
max_tokens for non-Latin scripts (.20-B); deep 7-section schema
with normalized digits + non-Latin Latin-anchor skip (.21);
7-section milan PDF download endpoint `POST /api/kundli-milan/pdf`
with NotoDeva auto-registration (.21-B). All entries in git history.
