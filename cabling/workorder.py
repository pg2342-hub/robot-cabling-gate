"""The work order for one rack: every connection the robot makes, with the port and label it must match.

Each shift in the pilot cables one rack of the pilot hall. Every rack uses the same template:
54 copper management connections (3 per compute tray, 18 trays) split over two management
switches, and 36 front-end fiber connections (2 DPU ports per tray). Both counts follow NVIDIA's
GB300 NVL72 reference design ("54 x 1Gb/s for management" per rack; one 2-port BlueField-3 DPU
per tray). Port names, labels, light levels and cycle-time targets are constructed for this demo.
"""

from __future__ import annotations

TRAYS = 18
COPPER_PER_TRAY = 3
FIBER_PER_TRAY = 2

# Cycle-time ceilings in seconds: a connection that takes longer than this counts as a miss.
CYCLE_CEILING_S = {"copper": 180, "fiber": 300}
# Lowest acceptable fiber receive power in dBm (illustrative).
MIN_RX_DBM = -7.0
MGMT_PORTS_PER_SWITCH = 27


def template() -> list[dict]:
    """The 90 connection slots of one rack, in the order the robot works them."""
    slots = []
    for tray in range(1, TRAYS + 1):
        for i in range(1, COPPER_PER_TRAY + 1):
            n = (tray - 1) * COPPER_PER_TRAY + i
            sw, port = divmod(n - 1, MGMT_PORTS_PER_SWITCH)
            slots.append(
                {
                    "slot": f"C{n:02d}",
                    "kind": "copper",
                    "tray": tray,
                    "device_port": f"T{tray:02d}-MGMT{i}",
                    "switch_port": f"MGMT-SW{sw + 1}/{port + 1}",
                    "label": f"T{tray:02d}-M{i}",
                }
            )
    for tray in range(1, TRAYS + 1):
        for i in range(1, FIBER_PER_TRAY + 1):
            n = (tray - 1) * FIBER_PER_TRAY + i
            slots.append(
                {
                    "slot": f"F{n:02d}",
                    "kind": "fiber",
                    "tray": tray,
                    "device_port": f"T{tray:02d}-DPU-P{i}",
                    "switch_port": f"FE-LEAF{1 + (n - 1) // 18}/{(n - 1) % 18 + 1}",
                    "label": f"T{tray:02d}-F{i}",
                }
            )
    return slots


def cases() -> list[dict]:
    """golive-gate cases: one per slot. The robot's log for that slot on a given shift is the output graded."""
    return [
        {
            "id": s["slot"],
            "group": s["kind"],
            "title": f"{s['device_port']} to {s['switch_port']}",
            "input": {"slot": s["slot"]},
            "expected": {
                "kind": s["kind"],
                "switch_port": s["switch_port"],
                "label": s["label"],
                "cycle_ceiling_s": CYCLE_CEILING_S[s["kind"]],
            },
        }
        for s in template()
    ]
