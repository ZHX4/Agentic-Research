#!/usr/bin/env bash
#
# Agentic-Research offline end-to-end release check (Phase 12).
#
# Runs the complete research chain without network access and without Docker:
#   demo -> validate -> gaps -> analyze -> fit-calibrator/calibrate
#   -> index -> retrieve -> traverse -> discover-gaps -> verify-gaps
#   -> reason -> plan -> evaluation -> autonomous (smoke) -> publication
#
# Notes on honesty:
# - verify-gaps uses --no-external (local world model only) and --no-deep-verify
#   (no full-text downloads), so verdicts stay conservative (inconclusive/uncertain
#   rather than false novelty). reason therefore runs with --min-gap-status
#   uncertain --allow-uncertain-gaps, which is the documented opt-in path.
# - `autonomous run --offline-smoke-test` exercises control-plane plumbing only;
#   it is not a scientific discovery claim (see docs/phase-9.md).
# - `execution execute` is intentionally skipped: it requires a Docker daemon.
#
set -euo pipefail

# Always run from the repository root regardless of caller CWD.
cd "$(dirname "${BASH_SOURCE[0]}")/.."

ART="artifacts/e2e"
rm -rf "$ART"
mkdir -p "$ART"

echo "==> [0] fixtures"
python - <<'EOF'
import json
from pathlib import Path

import fitz

art = Path("artifacts/e2e")

papers = [
    {
        "paper_id": "e2e-001",
        "title": "E2E Study A",
        "year": 2024,
        "authors": ["E2E Author"],
        "methods": ["E2E-Method-Alpha"],
        "tasks": ["e2e-task"],
        "datasets": ["E2E-Data-Alpha"],
    },
    {
        "paper_id": "e2e-002",
        "title": "E2E Study B",
        "year": 2024,
        "authors": ["E2E Author"],
        "methods": ["E2E-Method-Beta"],
        "tasks": ["e2e-task"],
        "datasets": ["E2E-Data-Beta"],
    },
]

corpus = art / "corpus.jsonl"
with corpus.open("w", encoding="utf-8") as handle:
    for paper in papers:
        handle.write(json.dumps(paper) + "\n")

for paper in papers:
    (art / f"{paper['paper_id']}.json").write_text(json.dumps(paper), encoding="utf-8")
    pdf_path = art / f"{paper['paper_id']}.pdf"
    document = fitz.open()
    page = document.new_page(width=600, height=800)
    page.insert_text((60, 60), paper["title"], fontsize=18)
    page.insert_text((60, 100), "Introduction", fontsize=16)
    page.insert_text((60, 130), "Retrieval systems can improve factual accuracy [1].")
    page.insert_text((60, 160), "Methods", fontsize=16)
    page.insert_text((60, 190), "We propose a retrieval method and evaluate it.")
    page.insert_text((60, 220), "Results", fontsize=16)
    page.insert_text((60, 250), "Our method improves accuracy over the baseline.")
    page.insert_text((60, 280), "References", fontsize=16)
    page.insert_text((60, 310), "[1] Alice Example. Retrieval Systems. 2024. doi:10.1234/XYZ")
    document.save(pdf_path)
    document.close()

(art / "labels.jsonl").write_text(
    json.dumps({"raw_confidence": 0.1, "correct": False})
    + "\n"
    + json.dumps({"raw_confidence": 0.9, "correct": True})
    + "\n",
    encoding="utf-8",
)

(art / "run.py").write_text("print('e2e experiment')\n", encoding="utf-8")

(art / "auto_in.json").write_text(
    json.dumps({"provenance_refs": ["e2e:input"]}), encoding="utf-8"
)
print("fixtures written")
EOF

echo "==> [1] demo / validate / gaps (Phase 0)"
python -m agentic_research.cli demo > /dev/null
python -m agentic_research.cli validate --input "$ART/corpus.jsonl"
python -m agentic_research.cli gaps --input "$ART/corpus.jsonl" --output "$ART/gaps.json"

echo "==> [2] analyze + calibration (Phase 2)"
python -m agentic_research.cli analyze \
    --paper "$ART/e2e-001.json" \
    --pdf "$ART/e2e-001.pdf" \
    --output "$ART/analysis-001.json"
python -m agentic_research.cli analyze \
    --paper "$ART/e2e-002.json" \
    --pdf "$ART/e2e-002.pdf" \
    --output "$ART/analysis-002.json"
python -m agentic_research.cli fit-calibrator \
    --input "$ART/labels.jsonl" \
    --output "$ART/calibrator.json"
python -m agentic_research.cli calibrate \
    --input "$ART/labels.jsonl" \
    --output "$ART/calibration.json"

echo "==> [3] index / retrieve / traverse (Phase 3)"
python -m agentic_research.cli index \
    --input "$ART/analysis-001.json" \
    --database "$ART/world.sqlite" \
    --embedding hash
python -m agentic_research.cli index \
    --input "$ART/analysis-002.json" \
    --database "$ART/world.sqlite" \
    --embedding hash
python -m agentic_research.cli retrieve "retrieval accuracy" \
    --database "$ART/world.sqlite" \
    --limit 5 \
    --mode hybrid \
    --embedding hash \
    --reranker lexical
python -m agentic_research.cli traverse "paper:e2e-001" \
    --database "$ART/world.sqlite" \
    --depth 1

echo "==> [4] discover-gaps (Phase 4)"
python -m agentic_research.cli discover-gaps \
    --database "$ART/world.sqlite" \
    --output "$ART/gaps4.json" \
    --min-entity-support 1 \
    --include-type missing_combination

echo "==> [5] verify-gaps, local only, no deep full text (Phase 5)"
python -m agentic_research.verification.cli \
    --input "$ART/gaps4.json" \
    --output "$ART/novelty.json" \
    --database "$ART/world.sqlite" \
    --no-external \
    --no-deep-verify

echo "==> [6] reason, accepting uncertain gaps explicitly (Phase 6)"
python -m agentic_research.hypotheses.cli \
    --input "$ART/novelty.json" \
    --output "$ART/hyp.json" \
    --max-evolution-generations 0 \
    --min-gap-status uncertain \
    --allow-uncertain-gaps
HYP_ID=$(python -c "import json; print(json.load(open('$ART/hyp.json'))['selected_hypothesis_ids'][0])")
echo "selected hypothesis: $HYP_ID"

echo "==> [7] plan (Phase 7; execute needs Docker and is skipped)"
python -m agentic_research.execution.cli plan \
    --hypothesis-run "$ART/hyp.json" \
    --hypothesis-id "$HYP_ID" \
    --code "$ART/run.py" \
    --command python \
    --command run.py \
    --primary-metric accuracy \
    --metric-direction higher \
    --output "$ART/exp.json"
python -m agentic_research.execution.cli tree \
    --spec "$ART/exp.json" \
    --output "$ART/exp.tree.json"

echo "==> [8] evaluation (Phase 8)"
python - <<'EOF'
import hashlib
import json
from pathlib import Path

art = Path("artifacts/e2e")


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


(art / "retrieval.cases.json").write_text(
    json.dumps(
        [
            {
                "case_id": "c1",
                "kind": "retrieval",
                "input_hash": h("c1"),
                "expected_ids": ["a", "b"],
            }
        ]
    ),
    encoding="utf-8",
)
(art / "retrieval.preds.json").write_text(
    json.dumps([{"case_id": "c1", "predicted_ids": ["a", "b"]}]), encoding="utf-8"
)
(art / "temporal.cases.json").write_text(
    json.dumps(
        [
            {
                "case_id": "t1",
                "kind": "temporal",
                "input_hash": h("t1"),
                "cutoff_year": 2020,
            }
        ]
    ),
    encoding="utf-8",
)
(art / "temporal.preds.json").write_text(
    json.dumps([{"case_id": "t1", "publication_years": {"a": 2019}}]), encoding="utf-8"
)
print("eval fixtures written")
EOF
python -m agentic_research.evaluation.cli retrieval \
    --cases "$ART/retrieval.cases.json" \
    --predictions "$ART/retrieval.preds.json" \
    --output "$ART/retrieval.json" \
    --system-name e2e
python -m agentic_research.evaluation.cli temporal \
    --cases "$ART/temporal.cases.json" \
    --predictions "$ART/temporal.preds.json" \
    --output "$ART/temporal.json" \
    --system-name e2e
python -m agentic_research.evaluation.cli report \
    --system-name e2e \
    --output "$ART/report.json" \
    --benchmark "$ART/retrieval.json" \
    --benchmark "$ART/temporal.json"

echo "==> [9] autonomous control-plane smoke test (Phase 9)"
python -m agentic_research.autonomy.cli run \
    --run-id e2e \
    --state-db "$ART/autonomy.sqlite" \
    --input-file "$ART/auto_in.json" \
    --output "$ART/auto_report.json" \
    --offline-smoke-test \
    --max-iterations 1

echo "==> [10] publication packaging (Phase 10)"
python - <<'EOF'
import json
from pathlib import Path

art = Path("artifacts/e2e")
(art / "arch.json").write_text(json.dumps({"evidence_refs": ["e2e:arch"]}), encoding="utf-8")
(art / "eval.json").write_text(
    json.dumps({"provenance_refs": ["e2e:bench"], "benchmarks": [{"benchmark_id": "b1"}]}),
    encoding="utf-8",
)
(art / "case.json").write_text(
    json.dumps(
        {
            "case_id": "e2e",
            "hypothesis": {"id": "h1"},
            "verification": {"id": "v1"},
            "execution": {"id": "e1"},
            "evaluation": {"id": "ev1"},
            "provenance_refs": ["e2e:case"],
        }
    ),
    encoding="utf-8",
)
(art / "disclosure.json").write_text(
    json.dumps(
        [
            {
                "provider": "e2e",
                "model": "synthetic-smoke",
                "role": "evaluation",
                "local_or_remote": "local",
                "training_data_disclosed": True,
                "usage_notes": "Offline release-check fixtures only.",
            }
        ]
    ),
    encoding="utf-8",
)
print("publication fixtures written")
EOF
python -m agentic_research.publication.cli manifest \
    --source-commit abcdef1234567890 \
    --artifacts "$ART/exp.json" \
    --kinds result \
    --licenses MIT \
    --artifacts "$ART/report.json" \
    --kinds result \
    --licenses MIT \
    --output "$ART/repro.json"
python -m agentic_research.publication.cli audit-license \
    --manifest-file "$ART/repro.json" \
    --output "$ART/audit.json"
python -m agentic_research.publication.cli write-manuscripts \
    --source-commit abcdef1234567890 \
    --architecture "$ART/arch.json" \
    --evaluation "$ART/eval.json" \
    --case-study "$ART/case.json" \
    --output-dir "$ART/manuscripts"
python -m agentic_research.publication.cli bundle \
    --source-commit abcdef1234567890 \
    --architecture "$ART/arch.json" \
    --evaluation "$ART/eval.json" \
    --case-study "$ART/case.json" \
    --disclosure "$ART/disclosure.json" \
    --reproducibility "$ART/repro.json" \
    --output "$ART/bundle.json"

echo "==> [11] release assertions"
python - <<'EOF'
import json
from pathlib import Path

art = Path("artifacts/e2e")
required = [
    "gaps.json",
    "analysis-001.json",
    "analysis-002.json",
    "calibrator.json",
    "world.sqlite",
    "gaps4.json",
    "novelty.json",
    "hyp.json",
    "exp.json",
    "exp.tree.json",
    "report.json",
    "auto_report.json",
    "repro.json",
    "bundle.json",
]
missing = [name for name in required if not (art / name).is_file()]
assert not missing, f"missing artifacts: {missing}"
bundle = json.loads((art / "bundle.json").read_text(encoding="utf-8"))
assert bundle["status"] == "ready", f"bundle not ready: {bundle['status']}"
hyp = json.loads((art / "hyp.json").read_text(encoding="utf-8"))
assert hyp["selected_hypothesis_ids"], "no hypothesis selected"
print(f"ALL E2E CHECKS PASSED (bundle={bundle['bundle_id']} status=ready)")
EOF
