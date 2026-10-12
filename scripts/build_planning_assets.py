#!/usr/bin/env python3
"""Render planning documents and editable Archi boards from the scenario catalog.

These outputs describe the local application; screenshots and traces supply execution evidence.
Regeneration replaces the generated catalog and board. Preserve hand-edited Archi
projects under another filename before regenerating them.
"""

import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
BLUE = "#e6f0ff"
GREEN = "#dff2e8"
ORANGE = "#fff0d9"
PURPLE = "#eee7fa"
RED = "#fbe6e6"
GRAY = "#edf1f5"


class View:
    def __init__(self, view_id, title, notes=""):
        self.value = {
            "id": view_id, "title": title, "notes": notes,
            "viewport": {"x": -40, "y": -40, "zoom": 0.62},
            "shapes": [], "arrows": [],
        }

    def box(self, x, y, text, color=BLUE, width=280, height=115,
            kind="process", description="", link=""):
        identifier = len(self.value["shapes"]) + 1
        self.value["shapes"].append({
            "shapeId": identifier, "px": x, "py": y, "pw": width, "ph": height,
            "text": text, "shapeColor": color, "shapeKind": kind,
            "nodeKey": f"{self.value['id']}-{identifier}",
            "description": description, "pseudocode": "", "linkView": link,
        })
        return identifier

    def edge(self, start, end, label="", points=None, label_at=None):
        edge = {"fromId": start, "toId": end, "label": label}
        if points:
            edge["points"] = [{"x": x, "y": y} for x, y in points]
        if label_at:
            edge["labelX"], edge["labelY"] = label_at
        self.value["arrows"].append(edge)


def scenario_view(scenario):
    view = View(scenario["id"], scenario["title"], scenario["story"])
    view.box(0, 0, scenario["title"] + "\nWorking local demonstration / real API transfers",
             GRAY, width=1740, height=85, description=scenario["actor"])
    view.box(0, 115, "BEFORE / Manual work across independently saved applications",
             ORANGE, width=1740, height=60)
    source = view.box(0, 220, "Read the source\nReport / file / request", ORANGE,
                      description="\n".join(scenario["sources"]))
    prior = source
    manual_indices = (0, 1, 2)
    for index, app in enumerate(scenario["apps"]):
        step = view.box(350 * (index + 1), 220,
                        app + "\nEnter / copy relevant fields", ORANGE,
                        description=scenario["manual"][manual_indices[index]])
        view.edge(prior, step, "read" if index == 0 else "re-enter",
                  label_at=(315 + 350 * index, 250))
        prior = step
    compare = view.box(1400, 220, "Check all three results\nCorrect mismatches", ORANGE,
                       description=scenario["manual"][-1])
    view.edge(prior, compare, "compare", label_at=(1365, 250))

    view.box(0, 395, "AFTER / One intake, explicit review, API writes, verified results",
             GREEN, width=1740, height=60)
    intake = view.box(0, 570, "Enter / import once\nExtract and map fields", BLUE,
                      description="\n".join(scenario["automated"][:1]))
    review = view.box(350, 550, "Ready to\ncontinue?", PURPLE,
                      height=155, kind="decision", description="\n".join(scenario["rules"]))
    worker = view.box(700, 570, "Run saved workflow\nOrder steps / keep IDs", GREEN,
                      description="\n".join(scenario["automated"][1:]))
    correction = view.box(350, 845, "Review / correct\nResolve this story's exception", RED,
                          description=scenario["failure"])
    view.edge(intake, review, "data", label_at=(314, 593))
    view.edge(review, worker, "ready", label_at=(665, 593))
    view.edge(review, correction, "needs review", label_at=(490, 773))
    view.edge(correction, review, "recheck", points=[(315, 900), (315, 625)],
              label_at=(280, 770))

    targets = []
    for index, app in enumerate(scenario["apps"]):
        y = 500 + 190 * index
        target = view.box(1050, y, f"{index + 1}. " + app + "\nSave through its API", BLUE,
                          description=scenario["demo_routes"][index]
                          + "\nImplemented local workplace endpoint; followed by a GET to verify the saved record.")
        targets.append(target)
        if index == 0:
            view.edge(worker, target, "write" if index == 0 else "",
                      points=[(1010, 627), (1010, y + 57)],
                      label_at=(1010, 526) if index == 0 else None)
        else:
            label = "saved ID"
            view.edge(targets[index - 1], target, label,
                      label_at=(1190, y - 38))
    proof = view.box(1430, 685, "Read back + inspect\nSaved IDs / files / evidence", GREEN,
                     width=310, height=140, description="\n".join(scenario["evidence"]))
    for index, target in enumerate(targets):
        y = 557 + 190 * index
        view.edge(target, proof, "", points=[(1380, y), (1380, 755)])
    failure = view.box(700, 1060, "Failed step? Keep completed IDs.\nReconcile, then resume safely.", RED,
                       width=1040, height=90, description=scenario["failure"])
    view.edge(worker, failure, "partial result", points=[(840, 1015)], label_at=(910, 994))
    view.box(0, 1220, "COST / SOURCE / SCALE\nSee node notes and docs/RESEARCH.md; no measured capacity claimed yet.",
             GRAY, width=1740, height=85,
             description=scenario["cost"] + "\n\n" + scenario["scale"])
    return view.value


def overview_view(scenarios):
    view = View("overview", "Showcase map", "Select a linked workplace card in Archi to open its before/after view.")
    view.box(0, 0, "AUTOMATION SHOWCASE\nRealistic work / visible proof / $0 required service charges",
             GRAY, width=1560, height=100)
    view.box(0, 135, "Each story: manual apps -> reset -> one intake -> real calls -> inspect outputs -> recover a failure",
             GREEN, width=1560, height=85)
    for index, scenario in enumerate(scenarios):
        view.box((index % 3) * 535, 275 + (index // 3) * 205,
                 scenario["title"], BLUE, width=490, height=160,
                 description=scenario["actor"] + "\n\n" + scenario["story"], link=scenario["id"])
    view.box(1070, 685, "How it is connected\nArchitecture and evidence", PURPLE,
             width=490, height=160, link="architecture")
    view.box(0, 905, "Working local apps + actual browser evidence. Public sources: Google Sheets and historical OpenF1.",
             ORANGE, width=1560, height=85)
    return view.value


def architecture_view():
    view = View("architecture", "Structure and evidence", "Implemented local service boundaries. Vendor products in the research are separate integration candidates.")
    view.box(0, 0, "ONE SHOWCASE / TWO VIEWS OF THE SAME RUN\nBusiness results and optional technical evidence",
             GRAY, width=1780, height=90)
    ui = view.box(0, 170, "Presenter workspace\nChoose / reset / compare", GREEN)
    ingest = view.box(370, 170, "Intake + profiles\nParse / map / review", BLUE)
    runner = view.box(740, 170, "Workflow service\nPersistent steps + queue", GREEN)
    adapters = view.box(1110, 170, "HTTP + file adapters\nLocal bearer / field schemas", PURPLE)
    targets = view.box(1480, 170, "Independent targets\nOwn APIs + stored records", BLUE)
    view.edge(ui, ingest, "input")
    view.edge(ingest, runner, "ready")
    view.edge(runner, adapters, "operations")
    view.edge(adapters, targets, "HTTP / tools")
    public = view.box(0, 490, "Public data provider\nSource IDs + freshness", BLUE)
    files = view.box(370, 490, "Document tools\nLocal extraction + output", BLUE)
    events = view.box(740, 490, "Step and evidence store\nRun IDs / results / errors", GREEN)
    access = view.box(1110, 490, "Local connection controls\nGrant / revoke / restore", PURPLE)
    tools = view.box(1480, 490, "Poppler + Tesseract\nCSV / XLSX / PDF / calendar", BLUE)
    view.edge(public, ingest, "fetch / cache", points=[(140, 415), (510, 415)])
    view.edge(ingest, files, "process files")
    view.edge(runner, events, "persist progress")
    view.edge(access, adapters, "credentials", label_at=(1250, 450))
    view.edge(adapters, tools, "provider contract", points=[(1320, 370), (1620, 370)],
              label_at=(1450, 350))
    results = view.box(0, 800, "Business view\nBefore / after / outputs", GREEN, width=440)
    technical = view.box(620, 800, "Technical view\nMappings / actual API activity", PURPLE, width=440)
    archive = view.box(1240, 800, "Evidence bundle\nScreenshots / diagrams / timings", GREEN, width=520)
    view.edge(events, results, "results", points=[(880, 715), (220, 715)], label_at=(470, 696))
    view.edge(events, technical, "trace", label_at=(915, 675))
    view.edge(events, archive, "export", points=[(880, 745), (1500, 745)], label_at=(1240, 724))
    view.box(0, 1010, "Recover by saved step and target ID. Verify writes through read-back. Measure capacity on owned local services.",
             ORANGE, width=1780, height=85)
    return view.value


def validate_board(board):
    views = board["views"]
    view_ids = {view["id"] for view in views}
    assert len(view_ids) == len(views)
    assert board["activeView"] in view_ids
    for view in views:
        ids = {node["shapeId"] for node in view["shapes"]}
        assert len(ids) == len(view["shapes"])
        for node in view["shapes"]:
            assert node["pw"] > 0 and node["ph"] > 0
            assert not node["linkView"] or node["linkView"] in view_ids
        for edge in view["arrows"]:
            assert edge["fromId"] in ids and edge["toId"] in ids


def write_catalog(data):
    lines = [
        "# Detailed workflow catalog", "", "Generated from [scenarios.json](scenarios.json).",
        "", "Status: eight implemented local workflows with actual browser evidence. Vendor products remain researched integration candidates.",
        "", "Provider capabilities and costs are documented in [RESEARCH.md](RESEARCH.md).",
        "Local API paths below are implemented workplace interfaces, not vendor endpoint claims.", "",
    ]
    for scene in data["scenarios"]:
        lines += [f"## {scene['title']}", "", f"**Person:** {scene['actor']}.", "", scene["story"], "",
                  f"![Before and after flowchart](../diagrams/{scene['id']}.png)", "",
                  "### Inputs and systems", ""]
        lines += ["- " + value for value in scene["sources"]]
        lines += ["", "**Apps:** " + " / ".join(scene["apps"]) + ".", "",
                  "**Repeated facts:** " + ", ".join(scene["shared_fields"]) + ".", ""]
        for field, heading in [("manual", "Manual workflow"), ("automated", "Automated workflow")]:
            lines += ["### " + heading, ""]
            lines += [f"{number}. {value}" for number, value in enumerate(scene[field], 1)]
            lines.append("")
        lines += ["### Mapping and operations", ""]
        lines += ["- " + value for value in scene["mapping_examples"]]
        lines += ["", "| Application | Implemented demo operation | Inspectable output |", "| --- | --- | --- |"]
        for app, route, output in zip(scene["apps"], scene["demo_routes"], scene["outputs"]):
            lines.append(f"| {app} | `{route}` | {output} |")
        lines += ["", "### Rules and failure demonstration", ""]
        lines += ["- " + value for value in scene["rules"]]
        lines += ["", "**Failure:** " + scene["failure"], "", "### Cost and scalability", "",
                  scene["cost"], "", scene["scale"], "",
                  "**Research entries:** " + ", ".join(f"`{key}`" for key in scene["research"]) + ".", "",
                  "### Before/after evidence", ""]
        lines += ["- " + value for value in scene["evidence"]]
        lines += ["", "Apply the ten-position [capture plan](EVIDENCE_PLAN.md) to this story.", ""]
    (ROOT / "docs/WORKFLOW_CATALOG.md").write_text("\n".join(lines), encoding="utf-8")


def export_pngs(board, binary):
    with tempfile.TemporaryDirectory(prefix="free-intro-archi-") as temp:
        temporary = Path(temp)
        runtime = temporary / "runtime"
        runtime.mkdir(mode=0o700)
        env = os.environ.copy()
        env.update({"QT_QPA_PLATFORM": "offscreen", "QT_QUICK_BACKEND": "software",
                    "QT_SCALE_FACTOR": "1", "XDG_RUNTIME_DIR": str(runtime),
                    "XDG_CONFIG_HOME": str(temporary / "config"),
                    "XDG_CACHE_HOME": str(temporary / "cache")})
        env.pop("ARCHI_ENTRY", None)
        for view in board["views"]:
            document = dict(board, activeView=view["id"])
            source = temporary / "export.archi.json"
            source.write_text(json.dumps(document), encoding="utf-8")
            target = ROOT / "diagrams" / f"{view['id']}.png"
            result = subprocess.run([str(binary), "--export-png", str(source), str(target)],
                                    env=env, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RuntimeError(f"Archi export failed for {view['id']}: {result.stderr}")
            header = target.read_bytes()[:24]
            if header[:8] != b"\x89PNG\r\n\x1a\n":
                raise RuntimeError(f"Unreadable PNG: {target}")
            width, height = struct.unpack(">II", header[16:24])
            print(f"Exported {target.name}: {width} x {height}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archi", type=Path, help="Optional existing Archi binary for PNG exports")
    args = parser.parse_args()
    data = json.loads((ROOT / "docs/scenarios.json").read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    assert len({scene["id"] for scene in scenarios}) == len(scenarios)
    for scene in scenarios:
        assert len(scene["apps"]) == len(scene["outputs"]) == len(scene["demo_routes"]) == 3
    board = {"format": "archi-brainstorm", "version": 1,
             "title": "Automation showcase: before and after", "backgroundColor": "#ffffff",
             "activeView": "hvac", "views": [overview_view(scenarios)]
             + [scenario_view(scene) for scene in scenarios] + [architecture_view()]}
    validate_board(board)
    (ROOT / "diagrams").mkdir(exist_ok=True)
    (ROOT / "diagrams/showcase.archi.json").write_text(json.dumps(board, indent=2) + "\n", encoding="utf-8")
    write_catalog(data)
    print(f"Validated {len(scenarios)} scenarios and {len(board['views'])} editable Archi views.", flush=True)
    if args.archi:
        export_pngs(board, args.archi.resolve())


if __name__ == "__main__":
    main()
