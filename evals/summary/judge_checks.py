"""Rule checks plus one Claude judge check: is every claim in the update supported by the fact sheet."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from checks import checks as rule_checks
from golive_gate import CheckSet, judge_check

from cabling.recorded import ROOT, Tape, recording_judge, replay_judge

JUDGE_TAPE = Tape(ROOT / "summary_judge.jsonl")
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

_grounded = judge_check(
    "claims_supported",
    "Every claim in the update is supported by the fact sheet, including what the gate decided and why the robot "
    "is or is not working unsupervised next week. It does not promise dates, savings or results the fact sheet "
    "does not contain.",
    judge=judge,
    render_case=lambda case: "Fact sheet:\n" + json.dumps(case.input, indent=2),
    render_output=lambda out: f"Subject: {out['subject']}\n\n{out['body']}",
    critical=True,
)


@checks.check("claims_supported", text=_grounded.text, critical=True)
def claims_supported(case, out):
    return _grounded.run(case, out)
