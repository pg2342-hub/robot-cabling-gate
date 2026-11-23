import json
from types import SimpleNamespace

import pytest

from cabling.claude import ClaudeTriage, ClaudeWeeklySummary
from cabling.recorded import Tape, key, recording, replay
from cabling.schema import MODES


class FakeClient:
    def __init__(self, payload, stop="end_turn"):
        self.payload, self.stop, self.calls = payload, stop, []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(
            stop_reason=self.stop,
            model="claude-opus-5-5",
            usage=SimpleNamespace(input_tokens=1000, output_tokens=100),
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload))],
        )


TAGS = {"failure_mode": "not_latched", "owner": "robot_team", "safety": False,
        "blocks_unsupervised": False, "needs_review": False, "summary": "Reseated C05."}  # fmt: skip


def test_triage_sends_guide_and_schema_and_prices_the_call():
    client = FakeClient(TAGS)
    out = ClaudeTriage(client=client)({"shift": 1, "rack": "R01", "note": "C05 not clicked in"})
    call = client.calls[0]
    assert "triage_guide" not in call["system"] and "failure_mode" in call["system"]
    assert call["output_config"]["format"]["schema"]["properties"]["failure_mode"]["enum"] == MODES
    assert out["failure_mode"] == "not_latched"
    assert out["_meta"]["cost_usd"] == pytest.approx((1000 * 4 + 100 * 20) / 1e6)


def test_refusal_and_cutoff_raise():
    for stop in ("refusal", "max_tokens"):
        with pytest.raises(RuntimeError):
            ClaudeTriage(client=FakeClient(TAGS, stop))({"shift": 1, "rack": "R01", "note": "x"})


def test_summary_prompt_carries_the_fact_sheet():
    client = FakeClient({"subject": "s", "body": "b"})
    ClaudeWeeklySummary(client=client)({"week": 2, "connections": 450})
    msg = client.calls[0]["messages"][0]["content"]
    assert '"connections": 450' in msg and "fact sheet" in client.calls[0]["system"]


def test_tape_records_then_replays_in_order(tmp_path):
    tape = Tape(tmp_path / "t.jsonl")
    n = iter(range(10))
    rec = recording(lambda x: {"n": next(n)}, tape)
    rec({"a": 1}), rec({"a": 1})
    play = replay(Tape(tmp_path / "t.jsonl"))
    assert [play({"a": 1})["n"], play({"a": 1})["n"]] == [0, 1]
    with pytest.raises(LookupError):
        play({"a": 1})
    assert key({"a": 1}) == key({"a": 1})
