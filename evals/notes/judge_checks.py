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
    "The summary is one sentence that states what the tech note says happened and what was done, and adds no "
    "cause, number, fix or outcome that the note and its context do not state.",
    judge=judge,
    # The judge sees exactly what the triage step saw: the shift, the rack and the setting, so naming the rack,
    # the robot doing the work or the tech stepping in is context, not an added detail.
    render_case=lambda case: (
        f"Context: a field tech wrote this note after stepping in during supervised robot cabling shift "
        f"{case.input['shift']}, rack {case.input['rack']}. The robot makes the connections and the tech "
        f"watches.\nTech note: {case.input['note']}"
    ),
    render_output=lambda out: out["summary"],
)


@checks.check("summary_faithful", text=_faithful.text)
def summary_faithful(case, out):
    return _faithful.run(case, out)
