"""Build the GitHub Pages demo in docs/ from the graded shifts and the recorded Claude runs. No API key needed.

docs/index.html        the pilot at a glance: stage timeline, weekly customer updates, note triage
docs/shifts/NN/        golive-gate report for each shift (every connection, every check)
docs/notes/            recorded Claude triage of 30 tech notes, 3 runs, with the judge's verdicts
docs/notes-baseline/   the keyword tagger the same gate blocks
docs/summary/          recorded weekly customer updates, graded
"""

import html
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from golive_gate import evaluate, run_eval
from golive_gate import report as golive_report

from cabling.recorded import ROOT as REC
from cabling.recorded import Tape

sys.path.insert(0, str(ROOT / "scripts"))
import run_shifts  # noqa: E402
from run_shifts import fresh_project  # noqa: E402

DOCS = ROOT / "docs"
REPO = "https://github.com/pg2342-hub/robot-cabling-gate"
GOLIVE = "https://github.com/pg2342-hub/golive-gate"
LABEL = {"go": "GO", "partial": "PARTIAL", "no-go": "NO-GO"}
e = html.escape


def grade(config: Path, out: Path) -> dict:
    # fresh_project reimports the project's modules, so each grading starts from a full recording
    # tape even though run_shifts already graded the notes project in this same process.
    p = fresh_project(config)
    result = run_eval(p.agent, p.cases, p.checks, runs=p.runs)
    outcome = evaluate(p.gate, result)
    golive_report.write(out, result, p.gate, outcome, agent=p.agent_ref)
    (out / "report.md").unlink(missing_ok=True)
    data = golive_report.to_dict(result, p.gate, outcome, agent=p.agent_ref)
    return {"data": data, "result": result}


def stats(result) -> dict:
    agent_cost = result.total_cost_usd
    judge_cost = result.total_judge_cost_usd
    lat = [cr.output.get("_meta", {}).get("latency_s") for cr in result.case_runs if isinstance(cr.output, dict)]
    lat = [x for x in lat if x is not None]
    n = len(result.case_runs)
    return {
        "calls": n,
        "agent_cost": agent_cost,
        "judge_cost": judge_cost,
        "mean_cost": agent_cost / max(n, 1),
        "mean_latency": sum(lat) / len(lat) if lat else None,
    }


CSS = """
.head h1{margin:40px 0 14px}
.head .lead{max-width:42em}
/* verdict: one row per gate, one square per shift, note or week */
.verdict{margin:36px 0 0;border:1px solid var(--rule);border-radius:16px;background:#fbfaf6;overflow:hidden}
.vhead{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 24px;padding:18px 24px;
border-bottom:1px solid var(--rule)}
.vhead h2{all:unset;font:400 22px/1.2 var(--serif)}
.vhead p{margin:0;color:var(--ink-2);font-size:15px}
.vhead p b{color:var(--ink)}
.vrow{display:grid;grid-template-columns:minmax(0,15em) minmax(0,1fr) 9em 7.5em;align-items:center;gap:20px;
padding:20px 24px}
.vrow+.vrow{border-top:1px solid var(--rule-soft)}
.vwho b{display:block;font:400 20px/1.2 var(--serif)}
.vwho span{display:block;color:var(--ink-2);font-size:14px;line-height:1.4;margin-top:4px}
.vwho a{color:inherit}
.strip{display:grid;grid-template-columns:repeat(30,minmax(0,1fr));gap:4px}
.strip.wide{gap:6px}
.cell{display:block;aspect-ratio:1;border-radius:4px;border:1.5px solid transparent;
transition:transform .2s var(--ease),box-shadow .2s}
.strip.wide .cell{grid-column:span 2;aspect-ratio:auto;height:100%;min-height:22px;border-radius:5px}
.cell.pass{background:var(--green)}
.cell.fail{background:var(--paper);border-color:var(--ink)}
.cell.part{background:var(--paper);border:1.5px dashed var(--ink)}
.cell.crit{background:var(--ink)}
a.cell:hover,a.cell:focus-visible{transform:translateY(-3px);box-shadow:0 6px 12px -6px rgb(27 26 23/.5)}
.vscore{font-variant-numeric:tabular-nums}
.vscore b{font:400 40px/1 var(--serif)}
.vscore span{display:block;color:var(--ink-2);font-size:13px;line-height:1.35;margin-top:4px}
.tag{justify-self:end;display:inline-flex;align-items:center;justify-content:center;min-height:32px;padding:0 14px;
border-radius:999px;border:1px solid var(--ink);font:500 13px/1 var(--mono);letter-spacing:.06em;white-space:nowrap;
background:var(--ink);color:var(--paper)}
.tag.go{background:var(--green-wash);border-color:var(--green-wash);color:var(--green)}
.tag.partial{background:transparent;color:var(--ink);border-style:dashed}
.tag.sm{min-height:24px;padding:0 10px;font-size:11.5px;vertical-align:1px}
.legend{display:flex;flex-wrap:wrap;gap:6px 20px;padding:14px 24px;border-top:1px solid var(--rule);color:var(--ink-2);
font-size:13px}
.legend span{display:inline-flex;align-items:center;gap:8px}
.legend i{width:12px;height:12px;border-radius:3px;border:1.5px solid transparent}
.legend .pass{background:var(--green)}.legend .fail{border-color:var(--ink)}.legend .crit{background:var(--ink)}
.legend .part{border:1.5px dashed var(--ink)}
/* the signature: the stage timeline, shift by shift */
.tl{margin:20px 0 0;border:1px solid var(--rule);border-radius:16px;background:#fbfaf6;padding:20px 24px 18px}
.tl-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px 24px;margin:0 0 6px}
.tl-head h2{all:unset;font:400 22px/1.2 var(--serif)}
.tl-head p{margin:0;color:var(--ink-2);font-size:15px;max-width:46em}
.tl-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tl-hint{display:none;margin:4px 0 8px;font-size:13px;color:var(--ink-2)}
.tl svg{display:block;width:100%;min-width:760px;height:auto;font-variant-numeric:tabular-nums}
.tl text{font-family:var(--sans);fill:var(--ink-2);font-size:12px}
.tl .lab{font-size:12.5px;fill:var(--ink)}
.tl .sub{font-size:11px}
.tl .mono{font-family:var(--mono);font-size:11px}
.tl .num{font-family:var(--mono);font-size:12px;fill:var(--ink)}
.tl .num.miss{font-weight:600;text-decoration:underline}
.tl .num.quiet{fill:var(--ink-2)}
.tl .go{fill:var(--green)}
.tl .nogo{fill:var(--ink)}
.tl .partial{fill:var(--paper);stroke:var(--ink);stroke-width:1.5;stroke-dasharray:3 2.5}
.tl .chip{font-family:var(--mono);font-size:10.5px;font-weight:500;letter-spacing:.04em}
.tl .chip.on-dark{fill:var(--paper)}
.tl .chip.on-light{fill:var(--ink)}
.tl .bar{fill:var(--green)}
.tl .cu{fill:none;stroke:var(--ink);stroke-width:1.25}
.tl .thr{stroke:var(--ink);stroke-width:1;stroke-dasharray:4 4}
.tl .grid{stroke:var(--rule);stroke-width:1}
.tl .sup{fill:rgb(27 26 23/.07)}
.tl .uns{fill:var(--green)}
.tl .band-t{font-size:11.5px;fill:var(--ink)}
.tl .band-t.light{fill:var(--paper)}
.tl .note{fill:var(--ink)}
.tl a .hit{fill:transparent}
.tl a:hover .hit,.tl a:focus-visible .hit{fill:rgb(27 26 23/.045)}
.tl a:focus-visible{outline:none}
.tl .legend{padding:12px 0 0;border:0}
.tl .legend .bar{background:var(--green)}
.tl .legend .cu{border-color:var(--ink);background:transparent}
.tl .legend .uns{background:var(--green)}.tl .legend .sup{background:rgb(27 26 23/.12)}
/* page body: content and a side column */
.layout{display:grid;grid-template-columns:minmax(0,1fr) 270px;gap:56px;align-items:start;margin-top:8px}
.side{position:sticky;top:24px;margin-top:64px;display:grid;gap:22px;font-size:14px;color:var(--ink-2)}
.side h3{margin:0 0 6px;font:500 13px/1.3 var(--sans);color:var(--ink)}
.side p{margin:0}
.side nav a{display:block;padding:5px 0;color:var(--ink-2);text-decoration:none;
border-bottom:1px solid var(--rule-soft)}
.side nav a:hover{color:var(--ink)}
.side pre{font-size:12px;margin:6px 0 0}
.note{color:var(--ink-2);font-size:15px;max-width:44em;margin-top:14px}
.point{font-size:17px;max-width:40em;margin:0}
.rule3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:0 0 8px}
.rule3 div{border:1px solid var(--rule);border-radius:16px;padding:16px 18px;background:#fbfaf6;font-size:14.5px}
.rule3 div:last-child{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.rule3 h3{margin:0 0 6px;font:400 19px/1.25 var(--serif)}
.rule3 p{margin:0;opacity:.9}
.checks{display:flex;flex-wrap:wrap;gap:6px;margin:0;padding:0;list-style:none}
.checks li{margin:0;font-size:14px;border:1px solid var(--rule);border-radius:999px;padding:4px 12px}
td{white-space:nowrap}
th{white-space:normal}
td.w{white-space:normal}
.shifts td.c,.shifts th.c{text-align:center}
.shifts .miss{text-decoration:underline;text-underline-offset:3px;font-weight:500}
.weeks{display:grid;gap:12px}
.week{border:1px solid var(--rule);border-radius:16px;background:#fbfaf6;padding:18px 22px}
.week h3{margin:0 0 8px;font:400 19px/1.3 var(--serif)}
.week p{margin:0 0 10px;font-size:15px;max-width:46em}
.week .sent{margin:0;font:400 12.5px/1.4 var(--mono);color:var(--ink-2)}
.week .sent b{color:var(--green);font-weight:500}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:0 0 16px}
.stats div{border:1px solid var(--rule);border-radius:16px;padding:14px 18px;background:#fbfaf6;font-size:13.5px;
color:var(--ink-2)}
.stats b{display:block;font:400 26px/1.15 var(--serif);color:var(--ink);font-variant-numeric:tabular-nums}
@media (max-width:1000px){
 .layout{grid-template-columns:minmax(0,1fr);gap:0}
 .side{position:static;margin-top:48px;order:2}
 .vrow{grid-template-columns:minmax(0,1fr) auto;gap:14px 16px}
 .vrow .strip{grid-column:1/-1;grid-row:2}
 .vscore{grid-row:3}.vrow .tag{grid-row:3}
 .rule3{grid-template-columns:1fr}
}
@media (max-width:640px){
 .vrow{padding:18px}.vhead,.legend{padding-left:18px;padding-right:18px}.tl{padding:16px 14px}
 .strip{gap:3px}.strip.wide{gap:4px}.cell{border-radius:2px;border-width:1px}
 .stats{grid-template-columns:1fr}
 .tl svg{min-width:960px}
 .tl-hint{display:block}
}
@media (prefers-reduced-motion:reduce){.cell{transition:none}}
"""


def tag(decision: str, small: bool = False) -> str:
    cls = {"go": "go", "partial": "partial"}.get(decision, "")
    return f'<span class="tag {cls}{" sm" if small else ""}">{LABEL[decision]}</span>'


def page(body: str, desc: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Robot Cabling Go-Live Gate</title><meta name="description" content="{e(desc)}">'
        f"<style>{CSS}</style></head><body><main>{body}</main>"
        "<script>const t=document.getElementById('tl-scroll');if(t)t.scrollLeft=t.scrollWidth;</script>"
        "</body></html>"
    )


def note_cells(data: dict, href: str) -> str:
    """One square per note (or week): passed every run, failed a run, or a critical failure."""
    crit = {c["id"] for c in data["checks"] if c["critical"]}
    out = []
    for c in data["cases"]:
        runs = c["runs"]
        passed = sum(r["passed"] for r in runs)
        if any(set(r["failed_checks"]) & crit for r in runs):
            st, word = "crit", "critical failure"
        elif passed == len(runs):
            st, word = "pass", "passed"
        else:
            st, word = "fail", f"failed {len(runs) - passed} of {len(runs)} runs"
        out.append(f'<a class="cell {st}" href="{href}" aria-label="{e(c["id"])} {e(c["title"])}: {word}"></a>')
    return "".join(out)


def score(data: dict) -> tuple[str, int, int]:
    by_run = data["summary"]["by_run"]
    vals = sorted({r["passed"] for r in by_run})
    s = str(vals[0]) if len(vals) == 1 else f"{vals[0]}-{vals[-1]}"
    crit = sum(len(v) for v in data["gate_result"]["critical_failures"].values())
    return s, by_run[0]["total"], crit


def vrow(who: str, sub: str, cells: str, sc: str, unit: str, badge: str, wide: bool = False) -> str:
    return f"""<div class="vrow">
  <div class="vwho"><b>{who}</b><span>{sub}</span></div>
  <div class="strip{" wide" if wide else ""}" role="group" aria-label="{e(who)}">{cells}</div>
  <div class="vscore"><b>{sc}</b><span>{unit}</span></div>
  {badge}
</div>"""


def timeline_svg(pilot: dict) -> str:
    """The stage timeline to scale: gate per shift, the two streaks against the 10-shift line, and the stage."""
    shifts, tl = pilot["shifts"], pilot["timeline"]
    n = len(shifts)
    req = 10
    left, width = 168, 1040
    cw = (width - left) / (n + 1)  # one extra column for the shift after the last
    x = [left + i * cw for i in range(n + 1)]
    out = []
    # stage during each shift is the stage the previous shift earned
    stage = ["supervised"] + [t["next_stage"] for t in tl]
    y_head, y_gate, y_note = 16, 30, 72
    y_base, unit = 244, 14.0  # streak chart baseline and pixels per shift of streak
    y_cu, y_fi = 268, 292
    rows_y = [344, 368, 392, 416]
    height = 428
    # row labels
    labels = [
        (y_gate + 17, "Shift gate", ""),
        (y_note + 4, "Blocking note", ""),
        (y_base - req * unit + 4, "Streaks", "GO, and copper only"),
        (y_cu + 13, "Copper stage", ""),
        (y_fi + 13, "Fiber stage", ""),
    ]
    for y, lab, sub in labels:
        out.append(f'<text class="lab" x="0" y="{y}">{lab}</text>')
        if sub:
            out.append(f'<text class="sub" x="0" y="{y + 15}">{sub}</text>')
    for y, lab in zip(
        rows_y, ["Copper first pass", "Fiber first pass", "Robot interventions", "Customer misses"], strict=True
    ):
        out.append(f'<text class="lab" x="0" y="{y}">{lab}</text>')
    # threshold line and baseline
    yt = y_base - req * unit
    out.append(f'<line class="grid" x1="{left}" x2="{width}" y1="{y_base}" y2="{y_base}"/>')
    out.append(f'<line class="thr" x1="{left}" x2="{width}" y1="{yt}" y2="{yt}"/>')
    out.append(f'<text class="mono" x="{left + 4}" y="{yt - 6}">10 in a row</text>')
    for i, (s, t) in enumerate(zip(shifts, tl, strict=True)):
        x0, cx = x[i], x[i] + cw / 2
        d = s["decision"]
        aria = (
            f"Shift {s['shift']}, rack {s['rack']}: {LABEL[d]}; GO streak {t['go_streak']}, copper streak "
            f"{t['copper_streak']}; copper {s['copper_first_pass']} of 54, fiber {s['fiber_first_pass']} of 36"
            + ("; blocking note" if t["blocking_note"] else "")
        )
        out.append(f'<a href="shifts/{s["shift"]:02d}/" aria-label="{e(aria)}">')
        out.append(f'<rect class="hit" x="{x0 + 1}" y="0" width="{cw - 2}" height="{height}" rx="6"/>')
        out.append(f'<text class="mono" x="{cx}" y="{y_head}" text-anchor="middle">{s["shift"]}</text>')
        sq = 30
        cls = {"go": "go", "no-go": "nogo", "partial": "partial"}[d]
        out.append(f'<rect class="{cls}" x="{cx - sq / 2}" y="{y_gate}" width="{sq}" height="{sq}" rx="5"/>')
        chip = {"go": "GO", "no-go": "NG", "partial": "P"}[d]
        tone = "on-light" if d == "partial" else "on-dark"
        out.append(f'<text class="chip {tone}" x="{cx}" y="{y_gate + 19}" text-anchor="middle">{chip}</text>')
        if t["blocking_note"]:
            out.append(f'<path class="note" d="M{cx - 6} {y_note + 5} L{cx} {y_note - 5} L{cx + 6} {y_note + 5} Z"/>')
        bw = min(14, cw * 0.28)
        g, c = t["go_streak"], t["copper_streak"]
        if g:
            out.append(
                f'<rect class="bar" x="{cx - bw - 1}" y="{y_base - g * unit}" width="{bw}" height="{g * unit}"/>'
            )
        if c:
            out.append(
                f'<rect class="cu" x="{cx + 1.5}" y="{y_base - c * unit + 0.75}" width="{bw - 1.5}" '
                f'height="{c * unit - 0.75}"/>'
            )
        out.append(f'<text class="mono" x="{cx - 2}" y="{y_base + 13}" text-anchor="end">{g}</text>')
        out.append(f'<text class="mono" x="{cx + 2}" y="{y_base + 13}" text-anchor="start">{c}</text>')
        vals = [
            (s["copper_first_pass"], s["copper_first_pass"] < 53),
            (s["fiber_first_pass"], s["fiber_first_pass"] < 35),
            (s["interventions"], False),
            (s["customer_caused"] or "", False),
        ]
        for y, (v, miss) in zip(rows_y, vals, strict=True):
            cls = "num miss" if miss else "num"
            out.append(f'<text class="{cls}" x="{cx}" y="{y}" text-anchor="middle">{v}</text>')
        out.append("</a>")
    # the shift after the last one: what the pilot earned
    xn = x[n] + cw / 2
    out.append(f'<text class="mono" x="{xn}" y="{y_head}" text-anchor="middle">{n + 1}</text>')
    out.append(f'<text class="sub" x="{xn}" y="{y_gate + 19}" text-anchor="middle">next</text>')
    # stage bands, one per lane, merged across runs of the same stage
    for lane, y in (("copper", y_cu), ("fiber", y_fi)):

        def unsup(st: str, lane: str = lane) -> bool:
            return st == "unsupervised" or (lane == "copper" and st.startswith("copper unsupervised"))

        i = 0
        while i <= n:
            j = i
            while j + 1 <= n and unsup(stage[j + 1]) == unsup(stage[i]):
                j += 1
            on = unsup(stage[i])
            x0, x1 = x[i] + 2, x[j] + cw - 2
            out.append(
                f'<rect class="{"uns" if on else "sup"}" x="{x0}" y="{y}" width="{x1 - x0}" height="18" rx="4"/>'
            )
            word = "Unsupervised" if on else "Supervised"
            if x1 - x0 < 80:
                word = "Unsup." if on else "Sup."
            light = " light" if on else ""
            out.append(f'<text class="band-t{light}" x="{x0 + 8}" y="{y + 13}">{word}</text>')
            i = j + 1
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Stage timeline across {n} shifts">'
        + "".join(out)
        + "</svg>"
    )


def main() -> None:
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    (DOCS / ".nojekyll").touch()

    have_notes = Tape(REC / "notes_agent.jsonl").exists()
    pilot = run_shifts.main(DOCS / "shifts")
    for d in (DOCS / "shifts").iterdir():
        (d / "report.md").unlink(missing_ok=True)
    have_summary = Tape(REC / "summary_agent.jsonl").exists()

    notes = grade(ROOT / "evals/notes/golive.yml", DOCS / "notes") if have_notes else None
    base = grade(ROOT / "evals/notes/golive.baseline.yml", DOCS / "notes-baseline")
    summ = grade(ROOT / "evals/summary/golive.yml", DOCS / "summary") if have_summary else None

    tl = {t["shift"]: t for t in pilot["timeline"]}
    shifts = pilot["shifts"]
    promoted = next((t["shift"] for t in pilot["timeline"] if t["next_stage"] == "unsupervised"), None)
    copper = next((t["shift"] for t in pilot["timeline"] if t["next_stage"].startswith("copper")), None)
    last = pilot["timeline"][-1]

    # verdict rows
    shift_cells = "".join(
        f'<a class="cell {({"go": "pass", "partial": "part"}).get(s["decision"], "crit")}" '
        f'href="shifts/{s["shift"]:02d}/" aria-label="Shift {s["shift"]}: {LABEL[s["decision"]]}"></a>'
        for s in shifts
    )
    stage_badge = '<span class="tag go">UNSUPERVISED</span>' if promoted else '<span class="tag">SUPERVISED</span>'
    rows = vrow(
        "Shift gate",
        f"One square per shift; {len(shifts)} racks, 90 connections each",
        shift_cells,
        str(last["go_streak"]),
        "GO shifts in a row<br>needs 10, no blocking note",
        stage_badge,
        wide=True,
    )
    if notes:
        sc, tot, crit = score(notes["data"])
        rows += vrow(
            "Note triage",
            "Claude tags 30 tech notes, 3 runs each",
            note_cells(notes["data"], "notes/"),
            sc,
            f"of {tot} notes passed per run<br>{crit} critical failures",
            tag(notes["data"]["decision"]),
        )
    sc, tot, crit = score(base["data"])
    rows += vrow(
        "Keyword tagger",
        'No model; the same notes and gate. <a href="notes-baseline/">Why it fails</a>',
        note_cells(base["data"], "notes-baseline/"),
        sc,
        f"of {tot} notes passed<br>{crit} critical failures",
        tag(base["data"]["decision"]),
    )
    if summ:
        sc, tot, crit = score(summ["data"])
        rows += vrow(
            "Weekly update",
            "Claude writes the customer update from each week's fact sheet",
            note_cells(summ["data"], "#weekly"),
            sc,
            f"of {tot} weekly updates sent<br>{crit} critical failures",
            tag(summ["data"]["decision"]),
        )

    if promoted:
        answer = (
            f"Yes, from shift {promoted + 1}. After shift {promoted} the GO streak reaches 10 with no blocking note."
        )
    else:
        answer = "Not yet. The GO streak has not reached 10, so the robot stays supervised."
    if copper and promoted and copper < promoted:
        answer += f" Copper reached 10 in a row first, after shift {copper}."
    stage_note = (
        "A PARTIAL shift is a fiber-only miss, so the copper streak kept going: copper reaches 10 in a row first, "
        "which is why the plan can promote copper alone at the readout while fiber stays supervised."
        if copper
        else ""
    )

    shift_rows = "".join(
        f"<tr><td><a href='shifts/{s['shift']:02d}/'>Shift {s['shift']}</a></td><td>{s['rack']}</td>"
        f"<td>{tag(s['decision'], True)}</td>"
        f"<td class='c{' miss' if s['copper_first_pass'] < 53 else ''}'>{s['copper_first_pass']} of 54</td>"
        f"<td class='c{' miss' if s['fiber_first_pass'] < 35 else ''}'>{s['fiber_first_pass']} of 36</td>"
        f"<td class='c'>{s['interventions']}</td><td class='c'>{'yes' if tl[s['shift']]['blocking_note'] else ''}</td>"
        f"<td class='c'>{tl[s['shift']]['go_streak']}</td><td class='c'>{s['customer_caused'] or ''}</td>"
        f"<td class='c'>{tl[s['shift']]['copper_streak']}</td><td class='w'>{tl[s['shift']]['next_stage']}</td></tr>"
        for s in shifts
    )

    if summ:
        cards = []
        for c in summ["data"]["cases"]:
            r = c["runs"][0]
            out = r["output"]
            fails = ", ".join(r["failed_checks"]) or "all checks passed"
            body = e(out["body"]).replace("\n", "<br>")
            state = "<b>sent</b>" if r["passed"] else "held"
            cards.append(
                f"<div class='week'><h3>{e(out['subject'])}</h3><p>{body}</p>"
                f"<p class='sent'>Gate: {state} ({e(fails)})</p></div>"
            )
        weekly = (
            "<p class='note' style='margin:0 0 16px'>Claude writes each week's update from that week's fact sheet; "
            "a rule check holds any number not in the sheet, and a Claude judge holds any unsupported claim. "
            f"Gate: {tag(summ['data']['decision'], True)} (<a href='summary/'>details</a>).</p>"
            f"<div class='weeks'>{''.join(cards)}</div>"
        )
    else:
        weekly = "<p class='note'>Claude live run pending. The rule checks run in CI today.</p>"

    if notes:
        st = stats(notes["result"])
        groups = {}
        for c in notes["data"]["cases"]:
            g = groups.setdefault(c["group"], [0, 0])
            g[0] += sum(r["passed"] for r in c["runs"])
            g[1] += len(c["runs"])
        grow = "".join(f"<tr><td>{g}</td><td>{p} of {t}</td></tr>" for g, (p, t) in groups.items())
        lat = f"{st['mean_latency']:.1f} s" if st["mean_latency"] else "n/a"
        triage = (
            "<p class='note' style='margin:0 0 16px'>30 constructed tech notes, 3 runs each. Claude tags each note "
            "(failure mode, owner, safety, blocks unsupervised work, needs review) and writes a one-line summary; "
            "rules grade the tags and a Claude judge grades the summary. "
            f"Gate: {tag(notes['data']['decision'], True)} (<a href='notes/'>every note and verdict</a>).</p>"
            f"<div class='stats'><div><b>{st['calls']}</b>triage calls</div>"
            f"<div><b>{lat}</b>mean per note, ${st['mean_cost']:.4f} each</div>"
            f"<div><b>${st['judge_cost']:.2f}</b>judge, in total</div></div>"
            f"<div class='scroll'><table><tr><th>Group</th><th>Passed every check (notes x 3 runs)</th></tr>{grow}"
            "</table></div>"
        )
    else:
        triage = (
            "<p class='note'>Claude live run pending. The rule checks and the keyword baseline below run in CI "
            "today.</p>"
        )
    triage += (
        f"<p class='note'>The same gate blocks a keyword tagger: {tag(base['data']['decision'], True)}. It misses "
        "safety notes that never say “e-stop” (<a href='notes-baseline/'>see why</a>).</p>"
    )

    body = f"""
<div class="head">
<h1>Robot Cabling Go-Live Gate</h1>
<p class="lead">A supervised pilot where a robot cables one rack per shift (54 copper management and 36 front-end
fiber connections) for 15 shifts. When can the robot work without a tech watching? Simulated data.</p>
</div>

<section class="verdict" aria-labelledby="verdict-h">
  <div class="vhead"><h2 id="verdict-h">Can the robot work unsupervised?</h2><p><b>{e(answer)}</b></p></div>
  {rows}
  <div class="legend"><span><i class="pass"></i>GO, or passed every run</span><span><i class="part"></i>PARTIAL</span>
  <span><i class="fail"></i>Failed a run</span><span><i class="crit"></i>NO-GO, or a critical failure</span>
  <span>Select a square to open its report.</span></div>
</section>

<section class="tl" id="timeline" aria-labelledby="tl-h">
  <div class="tl-head"><h2 id="tl-h">Stage timeline, shift by shift</h2>
  <p>Blocking notes from {e(pilot["blocking_notes_from"])}. Select a shift to see every connection.</p></div>
  <p class="tl-hint">Showing the latest shifts. Scroll back for shift 1 and the row labels.</p>
  <div class="tl-scroll" id="tl-scroll">{timeline_svg(pilot)}</div>
  <div class="legend"><span><i class="bar"></i>GO streak</span><span><i class="cu"></i>Copper streak</span>
  <span><i class="sup"></i>Supervised</span><span><i class="uns"></i>Unsupervised</span>
  <span>Underlined: below the GO line (53 copper, 35 fiber)</span></div>
</section>

<div class="layout">
<div class="content">

<h2 id="rules">How a shift is graded</h2>
<p class="point">Each shift is graded connection by connection:</p>
<ul class="checks" style="margin:14px 0 18px"><li>Right port</li><li>Latched</li><li>Link up</li><li>Label</li>
<li>Clean fiber end face</li><li>Fiber receive power</li><li>Cycle time</li><li>Nobody stepping in</li>
<li>No live cable disturbed</li></ul>
<div class="rule3">
  <div><h3>GO</h3><p>53 of 54 copper and 35 of 36 fiber connections right the first time, with no live cable (one
  already linked up, on this rack or a neighbor) disturbed.</p></div>
  <div><h3>Copper first</h3><p>A fiber-only miss is PARTIAL and lets copper go first. {e(stage_note)}</p></div>
  <div><h3>Unsupervised</h3><p>Ten GO shifts in a row, with no tech note that blocks unsupervised work, moves the
  robot to unsupervised shifts.</p></div>
</div>
<p class="note">Misses the customer's network team fixed are reported but not counted against the robot. Built on
<a href="{GOLIVE}">golive-gate</a>.</p>

<h2 id="shifts">Every shift</h2>
<div class="scroll"><table class="shifts"><tr><th>Shift</th><th>Rack</th><th>Gate</th>
<th class="c">Copper first pass</th><th class="c">Fiber first pass</th><th class="c">Robot interventions</th>
<th class="c">Blocking note</th>
<th class="c">GO streak</th><th class="c">Customer misses</th><th class="c">Copper streak</th><th>Next shift</th></tr>
{shift_rows}</table></div>

<h2 id="weekly">Weekly update to the customer</h2>
{weekly}

<h2 id="triage">Tech note triage</h2>
{triage}
</div>

<aside class="side" aria-label="About this build">
  <nav aria-label="On this page"><a href="#verdict-h">Verdict</a><a href="#timeline">Stage timeline</a>
  <a href="#rules">How a shift is graded</a><a href="#shifts">Every shift</a><a href="#weekly">Weekly update</a>
  <a href="#triage">Tech note triage</a></nav>
  <div><h3>Data</h3><p>Simulated. Port names, labels, light levels, cycle-time ceilings and every miss are made up;
  the 30 tech notes are constructed. Claude runs are replayed from <code>recordings/</code>, so no API key is
  needed.</p></div>
  <div><h3>Run it yourself</h3><p>Python 3.10+.</p><pre>pip install -e ".[dev]"
pytest -q
python scripts/run_shifts.py
python scripts/build_demo.py</pre></div>
  <div><a class="pill" href="{REPO}">Code on GitHub</a></div>
</aside>
</div>
"""
    desc = (
        "A go-live gate for a supervised robot cabling pilot: 15 shifts graded connection by connection, a stage "
        "timeline to unsupervised work, and Claude note triage and weekly updates under their own gates."
    )
    (DOCS / "index.html").write_text(page(body, desc))
    import subprocess

    pages = sorted(str(p) for p in DOCS.rglob("index.html"))
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "demo_chrome.py"), *pages, "--repo", "robot-cabling-gate"], check=True
    )
    print(f"demo written to docs/ (notes recorded: {have_notes}, summaries recorded: {have_summary})")


if __name__ == "__main__":
    main()
