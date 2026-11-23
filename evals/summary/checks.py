"""Checks on the weekly customer update. Every number must come from the fact sheet: a number
the shift logs do not support never reaches a customer executive."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from golive_gate import FAIL, PASS, CheckSet, Verdict

checks = CheckSet()
NUM = re.compile(r"\d+(?:\.\d+)?")
# Spelled-out numbers from ten up ("ninety-nine percent" reads as 90). One to nine are left out:
# "one rack" or "two weeks" are ordinary words in an update, and the judge reads them in context.
WORDS = {
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14", "fifteen": "15",
    "twenty": "20", "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
    "eighty": "80", "ninety": "90", "hundred": "100",
}  # fmt: skip
SPELLED = re.compile(r"\b(" + "|".join(WORDS) + r")\b", re.IGNORECASE)


def v(ok, reason=""):
    return Verdict(PASS, "") if ok else Verdict(FAIL, reason)


def _text(out):
    return f"{out['subject']}\n{out['body']}"


def _numbers(text: str) -> set[str]:
    """Digits, plus spelled-out numbers read as digits ("ninety-nine" gives 90)."""
    return set(NUM.findall(text)) | {WORDS[w.lower()] for w in SPELLED.findall(text)}


def allowed_numbers(facts: dict) -> set[str]:
    nums = set(NUM.findall(json.dumps(facts)))
    return nums | {n.rstrip("0").rstrip(".") for n in nums if "." in n}


@checks.check(
    "numbers_from_facts",
    text="Every number in the update appears in the week's fact sheet.",
    critical=True,
)
def numbers_from_facts(case, out):
    extra = sorted(_numbers(_text(out)) - allowed_numbers(case.input), key=float)
    return v(not extra, f"numbers not in the fact sheet: {', '.join(extra)}")


@checks.check("stage_stated", text="The update says whether next week is supervised or unsupervised.")
def stage_stated(case, out):
    stage = case.input["stage_next_week"]
    body = _text(out).lower()
    if stage == "unsupervised":
        return v("unsupervised" in body or "without a tech" in body, "does not say the robot goes unsupervised")
    return v(re.search(r"(?<!un)supervised", body) is not None, "does not say the robot stays supervised")


@checks.check("short", text="The update is under 120 words, with no bullet points.")
def short(case, out):
    words = len(out["body"].split())
    bullets = re.search(r"^\s*([-*•]|\d+\.)\s", out["body"], re.M)
    return v(words < 120 and not bullets, f"{words} words" + (", has bullets" if bullets else ""))
