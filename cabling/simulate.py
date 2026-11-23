"""Simulated robot shift logs for a 15-shift supervised pilot (three working weeks, one rack per shift).

Nothing here comes from a real robot. Every miss is planted by hand in PLAN so the gate's
decisions are easy to follow: early shifts fail, shift 5 is partial, and shifts 6 to 15 pass.
Normal cycle times are drawn from a fixed hash, so every run writes the same logs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .workorder import CYCLE_CEILING_S, template

SHIFTS = 15

# What went wrong on each shift, by slot. Every other slot is a clean first-pass connection.
PLAN: dict[int, dict[str, str]] = {
    1: {"C05": "not_latched", "C31": "not_latched", "C40": "label_wrong", "C12": "live_disturbance",
        "F03": "dirty_endface", "F17": "dirty_endface", "F22": "wrong_port"},
    2: {"C08": "not_latched", "C27": "robot_fault", "F09": "damaged_cable", "F30": "customer_config"},
    3: {"C44": "not_latched", "C50": "slow", "F11": "dirty_endface"},
    4: {"C19": "robot_fault", "C02": "not_latched"},
    5: {"C33": "short_cable", "F05": "dirty_endface", "F28": "label_wrong"},
    6: {"F14": "damaged_cable", "F31": "vision_retry"},
    7: {"C21": "label_wrong"},
    8: {"F35": "customer_config"},
    9: {"C47": "slow"},
    10: {},
    11: {"C10": "not_latched", "F20": "low_light"},
    12: {},
    13: {"C38": "robot_fault"},
    14: {"F02": "dirty_endface"},
    15: {},
}  # fmt: skip

# The robot stopped because a person was in its work zone or someone pressed the stop. Not a miss in the
# shift gate; the tech's note on each one is triaged (evals/notes), and a note that blocks unsupervised
# work resets the pilot's GO streak (cabling/stages.py).
SAFETY_STOPS = {2: ["C15"], 3: ["C20"], 4: ["F07"], 12: ["C29"]}

INTERVENTION = {
    "not_latched": ("tech", "reseated the connector"),
    "wrong_port": ("tech", "moved the cable to the mapped port"),
    "dirty_endface": ("tech", "cleaned the end face and re-inspected"),
    "damaged_cable": ("tech", "swapped in a new jumper from spares"),
    "short_cable": ("tech", "swapped in a longer cord from spares"),
    "low_light": ("tech", "re-cleaned and reseated; receive power back in range"),
    "label_wrong": ("tech", "replaced the label"),
    "customer_config": ("customer_network", "fixed the port map or switch configuration; robot re-ran it"),
    "robot_fault": ("tech", "finished the connection by hand after a gripper fault"),
    "live_disturbance": ("tech", "reseated a live neighbor cable the robot knocked loose"),
}


def _jitter(*parts: object) -> float:
    h = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def rack_id(shift: int) -> str:
    return f"R{shift:02d}"


def log_for(shift: int) -> list[dict]:
    rack = rack_id(shift)
    plan = PLAN[shift]
    rows = []
    for s in template():
        slot, kind = s["slot"], s["kind"]
        base = 70 if kind == "copper" else 120
        spread = 50 if kind == "copper" else 90
        row = {
            "shift": shift,
            "rack": rack,
            "slot": slot,
            "kind": kind,
            "switch_port": s["switch_port"],
            "latched": True,
            "link_up": True,
            "label_scanned": f"{rack}-{s['label']}",
            "endface_inspection": "pass" if kind == "fiber" else None,
            "rx_dbm": round(-2.0 - 2.0 * _jitter("rx", shift, slot), 2) if kind == "fiber" else None,
            "cycle_s": round(base + spread * _jitter(shift, slot), 1),
            "intervention": None,
            "robot_retries": 0,
            "disturbed_live_neighbor": False,
            "safety_stop": slot in SAFETY_STOPS.get(shift, []),
        }
        event = plan.get(slot)
        if event == "not_latched":
            row.update(latched=False, link_up=False)
        elif event == "wrong_port":
            n = int(s["switch_port"].split("/")[1])
            row["switch_port"] = s["switch_port"].replace(f"/{n}", f"/{n % 18 + 1}")
        elif event == "dirty_endface":
            row["endface_inspection"] = "fail_cleaned"
        elif event == "label_wrong":
            row["label_scanned"] = f"{rack}-{s['label'][:-1]}{int(s['label'][-1]) % 3 + 1}"
        elif event == "customer_config":
            row["link_up"] = False
        elif event == "low_light":
            row["rx_dbm"] = -9.4
        elif event == "robot_fault":
            row["cycle_s"] = round(CYCLE_CEILING_S[kind] * 1.4, 1)
            row["robot_retries"] = 3
        elif event == "vision_retry":  # the robot recovered on its own, inside the cycle-time ceiling
            row["cycle_s"] = round(CYCLE_CEILING_S[kind] * 0.9, 1)
            row["robot_retries"] = 2
        elif event == "live_disturbance":
            row["disturbed_live_neighbor"] = True
        elif event == "slow":
            row["cycle_s"] = round(CYCLE_CEILING_S[kind] * 1.25, 1)
        if event in INTERVENTION:
            by, action = INTERVENTION[event]
            row["intervention"] = {"by": by, "action": action}
        rows.append(row)
    return rows


def write_all(out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for shift in range(1, SHIFTS + 1):
        p = out / f"shift_{shift:02d}.jsonl"
        p.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in log_for(shift)))
        paths.append(p)
    return paths


def load(path: Path) -> dict[str, dict]:
    return {r["slot"]: r for r in (json.loads(x) for x in path.read_text().splitlines() if x.strip())}
