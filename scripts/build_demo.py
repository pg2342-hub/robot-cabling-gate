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
:root{--fg:#000;--bg:#fff;--mute:#555;--line:#ddd}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 Inter,system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:26px;margin:0 0 6px}h2{font-size:18px;margin:36px 0 8px}p{margin:8px 0}
a{color:#000}.mute{color:var(--mute)}.tag{display:inline-block;border:1px solid #000;padding:0 6px;font-size:12px;
font-weight:600}.tag.go{background:#000;color:#fff}.tag.partial{border-style:dashed}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;margin:8px 0}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top;white-space:nowrap}
td.w{white-space:normal}th{font-weight:600}.card{border:1px solid #000;padding:12px 14px;margin:10px 0}
.card h3{font-size:15px;margin:0 0 4px}
"""


def tag(decision: str) -> str:
    cls = {"go": "go", "partial": "partial"}.get(decision, "")
    return f'<span class="tag {cls}">{LABEL[decision]}</span>'


def page(body: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Robot cabling go-live gate</title>"
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">'
        f"<style>{CSS}</style></head><body><main>{body}</main></body></html>"
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
    rows = "".join(
        f"<tr><td><a href='shifts/{s['shift']:02d}/'>Shift {s['shift']}</a></td><td>{s['rack']}</td>"
        f"<td>{tag(s['decision'])}</td><td>{s['copper_first_pass']} of {s['copper_total']}</td>"
        f"<td>{s['fiber_first_pass']} of {s['fiber_total']}</td><td>{s['interventions']}</td>"
        f"<td>{'yes' if tl[s['shift']]['blocking_note'] else ''}</td><td>{tl[s['shift']]['go_streak']}</td>"
        f"<td>{s['customer_caused'] or ''}</td><td>{tl[s['shift']]['copper_streak']}</td>"
        f"<td>{tl[s['shift']]['next_stage']}</td></tr>"
        for s in pilot["shifts"]
    )
    promoted = next((t["shift"] for t in pilot["timeline"] if t["next_stage"] == "unsupervised"), None)
    copper = next((t["shift"] for t in pilot["timeline"] if t["next_stage"].startswith("copper")), None)
    stage_line = (
        f"After shift {promoted} the GO streak reaches 10, so the robot works unsupervised from shift {promoted + 1}."
        if promoted
        else "The GO streak has not reached 10, so the robot stays supervised."
    )
    if copper:
        stage_line = (
            "A PARTIAL shift is a fiber-only miss, so the copper streak kept going: copper reaches 10 in a row "
            "first, which is why the plan can promote copper alone at the readout while fiber stays supervised. "
            + stage_line
        )

    if summ:
        cards = []
        for c in summ["data"]["cases"]:
            r = c["runs"][0]
            out = r["output"]
            fails = ", ".join(r["failed_checks"]) or "all checks passed"
            body = e(out["body"]).replace("\n", "<br>")
            cards.append(
                f"<div class='card'><h3>{e(out['subject'])}</h3><p>{body}</p>"
                f"<p class='mute'>Gate: {'sent' if r['passed'] else 'held'} ({e(fails)})</p></div>"
            )
        weekly = (
            f"<p>Claude writes each week's update from that week's fact sheet; a rule check holds any number not in "
            f"the sheet, and a Claude judge holds any unsupported claim. Gate: {tag(summ['data']['decision'])} "
            f"(<a href='summary/'>details</a>).</p>" + "".join(cards)
        )
    else:
        weekly = "<p class='mute'>Claude live run pending. The rule checks run in CI today.</p>"

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
            f"<p>30 constructed tech notes, 3 runs each. Claude tags each note (failure mode, owner, safety, "
            f"blocks unsupervised work, needs review) and writes a one-line summary; rules grade the tags and a "
            f"Claude judge grades the summary. Gate: {tag(notes['data']['decision'])} "
            f"(<a href='notes/'>every note and verdict</a>).</p>"
            f"<p class='mute'>{st['calls']} triage calls, mean {lat} and ${st['mean_cost']:.4f} per note; "
            f"judge ${st['judge_cost']:.2f} in total.</p>"
            f"<div class='wrap'><table><tr><th>Group</th><th>Passed every check (notes x 3 runs)</th></tr>{grow}"
            f"</table></div>"
        )
    else:
        triage = (
            "<p class='mute'>Claude live run pending. The rule checks and the keyword baseline below run in CI "
            "today.</p>"
        )
    triage += (
        f"<p>The same gate blocks a keyword tagger: {tag(base['data']['decision'])}. It misses safety notes that "
        f"never say “e-stop” (<a href='notes-baseline/'>see why</a>).</p>"
    )

    body = f"""
<h1>Robot cabling go-live gate</h1>
<p class="mute">Simulated data. A supervised pilot where a robot cables one rack per shift (54 copper management
and 36 front-end fiber connections) for 15 shifts.</p>
<p>When can the robot work without a tech watching? Each shift is graded connection by connection: right port,
latched, link up, label, clean fiber end face, fiber receive power, cycle time, nobody stepping in, and no
live cable disturbed. The gate says GO only when 53 of 54 copper and 35 of 36 fiber connections are right the
first time with no live cable (one already linked up, on this rack or a neighbor) disturbed. Misses the
customer's network team fixed are reported but not counted against the robot. Ten GO shifts in a row, with no
tech note that blocks unsupervised work, moves the robot to unsupervised shifts; a fiber-only miss lets copper
go first. Built on <a href="https://github.com/pg2342-hub/golive-gate">golive-gate</a>. <a href="{REPO}">Code
on GitHub</a>.</p>
<h2>Stage timeline</h2>
<p>{e(stage_line)} <span class="mute">Blocking notes from {e(pilot["blocking_notes_from"])}.</span></p>
<div class="wrap"><table><tr><th>Shift</th><th>Rack</th><th>Gate</th><th>Copper first pass</th>
<th>Fiber first pass</th><th>Robot interventions</th><th>Blocking note</th><th>GO streak</th>
<th>Customer misses</th><th>Copper streak</th><th>Next shift</th></tr>
{rows}</table></div>
<h2>Weekly update to the customer</h2>
{weekly}
<h2>Tech note triage</h2>
{triage}
"""
    (DOCS / "index.html").write_text(page(body))
    print(f"demo written to docs/ (notes recorded: {have_notes}, summaries recorded: {have_summary})")


if __name__ == "__main__":
    main()
