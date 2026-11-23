"""Rule checks plus one Claude judge check for what a rule cannot state: is the summary faithful to the note.

The judge runs live (and records each reply) when GOLIVE_LIVE=1 and replays the recording
otherwise, so CI and the demo page need no API key.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from checks import checks as rule_checks
from golive_gate import CheckSet, judge_check

from cabling.recorded import ROOT, Tape, recording_judge, replay_judge

JUDGE_TAPE = Tape(ROOT / "notes_judge.jsonl")
_judge = None


def judge(prompt):
    global _judge
    if _judge is None:
        if os.environ.get("GOLIVE_LIVE") == "1":
            from golive_gate import ClaudeJudge

            _judge = recording_judge(ClaudeJudge(model="claude-opus-5-5", effort="low"), JUDGE_TAPE)
        else:
            _judge = replay_judge(JUDGE_TAPE)
    return _judge(prompt)


checks = CheckSet(rule_checks)

_faithful = judge_check(
    "summary_faithful",
    "The summary is one sentence that restates the tech note: what happened and, if the note says, what was done. "
    "It fails if it adds a cause, number, fix, actor or outcome that the note does not state or clearly imply, or "
    "if it contradicts the note. Plain paraphrase, expanding shorthand the note clearly means (a slot name such "
    "as C19 is the connection being made; the map is the customer's port map) and naming the rack are fine.",
    judge=judge,
    render_case=lambda case: (
        f"Context: a field tech wrote this note during supervised robot cabling shift {case.input['shift']}, "
        f"rack {case.input['rack']}. The robot makes the connections and the tech watches and steps in when "
        f"needed. Slot names like C05 (copper) and F22 (fiber) are connections on the rack.\n"
        f"Tech note: {case.input['note']}"
    ),
    render_output=lambda out: out["summary"],
)


@checks.check("summary_faithful", text=_faithful.text)
def summary_faithful(case, out):
    return _faithful.run(case, out)
