"""Agents for the weekly update: recorded (no key) and live (records to recordings/)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from golive_gate import Response

from cabling.recorded import ROOT, Tape, recording, replay

TAPE = Tape(ROOT / "summary_agent.jsonl")
_live = None


def _as_response(record):
    return Response(record, cost_usd=record.get("_meta", {}).get("cost_usd", 0.0))


def recorded_summary(case_input):
    return _as_response(replay(TAPE)(case_input))


def live_summary(case_input):
    global _live
    if _live is None:
        from cabling.claude import ClaudeWeeklySummary

        _live = recording(ClaudeWeeklySummary(), TAPE)
    return _as_response(_live(case_input))


def invented_numbers(case_input):
    """A stand-in writer that rounds and projects. The gate must block it."""
    return {
        "subject": f"Week {case_input['week']}: about 99% first pass, unsupervised in two weeks",
        "body": "The robot is close to 99% first-pass yield and should save roughly 40% of tech hours. "
        "We expect to go unsupervised in two weeks.",
    }
