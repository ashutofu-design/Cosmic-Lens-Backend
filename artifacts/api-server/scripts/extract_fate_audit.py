"""Extract fate_line payload from agent transcript line."""
import json
import re
import sys
from pathlib import Path

transcript = Path(
    r"C:\Users\HP\.cursor\projects\d-Cosmic-Lens-Backend\agent-transcripts"
    r"\ccaa235b-3107-4723-b2dc-b950dc1c02f6\ccaa235b-3107-4723-b2dc-b950dc1c02f6.jsonl"
)
if not transcript.exists():
    print("transcript missing", file=sys.stderr)
    sys.exit(1)

for i, line in enumerate(transcript.read_text(encoding="utf-8").splitlines(), 1):
    if i < 433:
        continue
    if "fate_line" not in line and "check pls" not in line:
        continue
    print("LINE", i, "len", len(line))
    # try parse outer jsonl
    try:
        row = json.loads(line)
        text = row.get("message", {}).get("content", [])
        if isinstance(text, list):
            for part in text:
                if part.get("type") == "text":
                    body = part.get("text", "")
                    if "fate_line" in body:
                        # find JSON blob
                        for m in re.finditer(r"\{[\s\S]{500,}\}", body):
                            snippet = m.group(0)
                            try:
                                data = json.loads(snippet)
                                print(json.dumps(data.get("major_lines", {}).get("fate_line", data), indent=2)[:8000])
                            except json.JSONDecodeError:
                                pass
    except json.JSONDecodeError:
        pass
    # raw search
    for key in ["fate_line_detection", "candidate_audit", "image_support"]:
        idx = line.find(key)
        if idx >= 0:
            print("RAW around", key, ":", line[idx:idx+1200])
