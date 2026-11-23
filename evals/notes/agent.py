"""Agents for the notes gate.

- recorded_triage: replays the last live Claude run from recordings/ (no key; CI and the demo use this)
- live_triage:     calls Claude now and appends each record to recordings/ (needs ANTHROPIC_API_KEY)
- keyword_triage:  the no-model baseline the gate must block
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from golive_gate import Response

from cabling.baseline import keyword_triage as _keyword
from cabling.recorded import ROOT, Tape, recording, replay

TAPE = Tape(ROOT / "notes_agent.jsonl")
_live = None


def _as_response(record):
    return Response(record, cost_usd=record.get("_meta", {}).get("cost_usd", 0.0))


def recorded_triage(case_input):
    return _as_response(replay(TAPE)(case_input))


def live_triage(case_input):
    global _live
    if _live is None:  # created on first use, so importing this file needs no key
        from cabling.claude import ClaudeTriage

        _live = recording(ClaudeTriage(), TAPE)
    return _as_response(_live(case_input))


def keyword_triage(case_input):
    return _keyword(case_input)
