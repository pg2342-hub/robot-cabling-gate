"""The "agent" for the shift gate is the robot: each shift's log is replayed slot by slot.

golive run evals/shift/golive.yml --agent agent:shift_07   grades shift 7
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cabling.simulate import load

LOGS = ROOT / "data" / "shifts"
_cache: dict[int, dict] = {}


def _replay(shift: int):
    def robot(case_input):
        if shift not in _cache:
            _cache[shift] = load(LOGS / f"shift_{shift:02d}.jsonl")
        return _cache[shift][case_input["slot"]]

    robot.__name__ = f"shift_{shift:02d}"
    return robot


def __getattr__(name):
    if name.startswith("shift_") and name[6:].isdigit():
        return _replay(int(name[6:]))
    raise AttributeError(name)
