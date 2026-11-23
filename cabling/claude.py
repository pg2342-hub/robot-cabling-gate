"""The two Claude steps: triage one intervention note, and write the weekly customer summary.

Both use structured output, so the shape is guaranteed; rules and a separate judge grade the
content. Neither step grades itself. Reads the key from ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .schema import SUMMARY_SCHEMA, TRIAGE_SCHEMA

HERE = Path(__file__).parent
MODEL = "claude-opus-5-5"
EFFORT = "low"
# USD per million tokens (input, output), first-party list prices.
PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00), "claude-haiku-5-5": (0.10, 0.50)}

TRIAGE_SYSTEM = (
    "You triage field notes from a supervised robot cabling pilot in an AI data center. "
    "Follow the guide exactly and return one record per note.\n\n"
    f"<guide>\n{(HERE / 'triage_guide.md').read_text()}</guide>"
)

SUMMARY_SYSTEM = (
    "You write the weekly update a robotics deployment lead sends to the customer's data center operations "
    "executive during a supervised robot cabling pilot. Use only the numbers in the fact sheet, written exactly "
    "as they appear there; do not compute new ones such as percentages or differences, and do not forecast "
    "when the streak will reach the threshold or how many shifts are left. Say plainly whether the robot "
    "works supervised or unsupervised next week and why, in terms of the gate. Under 120 words, no bullet "
    "points, no greeting or sign-off, plain and factual."
)


class _ClaudeStep:
    schema: dict = {}
    system: str = ""

    def __init__(self, model: str = MODEL, effort: str = EFFORT, client: Any = None) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client, self.model, self.effort = client, model, effort

    def message(self, case_input: dict) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    def __call__(self, case_input: dict) -> dict:
        start = time.perf_counter()
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": self.schema}},
            system=self.system,
            messages=[{"role": "user", "content": self.message(case_input)}],
        )
        latency = time.perf_counter() - start
        if response.stop_reason == "refusal":
            raise RuntimeError("the model declined this input")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("the record was cut off at max_tokens")
        record = json.loads(next(b.text for b in response.content if b.type == "text"))
        record["_meta"] = {
            "model": getattr(response, "model", self.model),
            "cost_usd": self.cost(response),
            "latency_s": round(latency, 3),
        }
        return record

    def cost(self, response: Any) -> float:
        price = PRICES.get(getattr(response, "model", self.model)) or PRICES.get(self.model)
        if not price:
            return 0.0
        u = response.usage
        return round((u.input_tokens * price[0] + u.output_tokens * price[1]) / 1_000_000, 6)


class ClaudeTriage(_ClaudeStep):
    schema, system = TRIAGE_SCHEMA, TRIAGE_SYSTEM

    def message(self, case_input: dict) -> str:
        return f"Shift {case_input['shift']}, rack {case_input['rack']}.\nTech note: {case_input['note']}"


class ClaudeWeeklySummary(_ClaudeStep):
    schema, system = SUMMARY_SCHEMA, SUMMARY_SYSTEM

    def message(self, case_input: dict) -> str:
        return f"<fact_sheet>\n{json.dumps(case_input, indent=2)}\n</fact_sheet>\n\nWrite this week's update."
