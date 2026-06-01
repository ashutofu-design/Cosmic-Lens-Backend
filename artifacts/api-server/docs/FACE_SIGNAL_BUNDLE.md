# FaceSignalBundle — compressed AI input

## Flow

```
engines + sections (analyze)
    → build_face_signal_bundle()
    → stored: session.report_payload.signal_bundle + face:analysis:{id}
PDF / enrich_face_narratives
    → load_bundle_for_analysis()
    → ONE bundle JSON in OpenAI user prompt
    → per-section: GOAL + 3–5 focus signals only
```

## Example bundle JSON

```json
{
  "version": "sig_v1",
  "personality": {
    "archetype": {"value": "Strategic Observer", "confidence": 0.71},
    "core_type": {"value": "structured disciplined leaning", "confidence": 0.68}
  },
  "communication": {
    "public_read": {"value": "approachable first read", "confidence": 0.62},
    "warmth": {"value": "selectively warm", "confidence": 0.58}
  },
  "attachment": {
    "style": {"value": "selective depth", "confidence": 0.6},
    "friction": {"value": "occasional reassurance needs", "confidence": 0.55}
  },
  "contradictions": [
    {
      "tension": "warm but guarded",
      "note": "Social spark with selective trust.",
      "confidence": 0.72
    }
  ],
  "strengths": ["Reliable follow-through under pressure"],
  "blind_spots": ["Overthinking before acting"],
  "confidence_levels": {
    "overall": 0.68,
    "note": "moderate"
  },
  "anchors": ["Strategic Observer", "oval", "prithvi", "C"]
}
```

## Token savings

Logs on each AI batch:

```
[face_ai] prompt facts ~3200B vs legacy ~12400B (~74% smaller)
```

Legacy = repeated `_engine_highlights` + `_flatten_facts` per section.  
New = one shared bundle + ~4 lines per section.

## Files

- `vedic/face_reading/face_signal_bundle.py` — build, validate, section routing
- `vedic/face_reading/ai_narrator.py` — prompts use bundle only
- `flask_app.py` — builds bundle at end of `analyze`

## Cache version

`FACE_CACHE_VERSION=face-v6-signal-bundle` — bump invalidates old narration disk cache.
