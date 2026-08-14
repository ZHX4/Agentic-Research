"""CLI for Phase 10 publication and release packaging."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, TypeVar

import typer
from pydantic import BaseModel

from agentic_research.publication.engine import (
    audit_licenses,
    build_artifact_entry,
    build_case_study,
    build_publication_bundle,
    build_reproducibility_package,
    build_system_paper,
)
from agentic_research.schemas.phase10 import ModelProviderDisclosure

app = typer.Typer(help="Agentic-Research Phase 10 publication pipeline.")
T = TypeVar("T", bound=BaseModel)


def _read(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise typer.BadParameter(f"{path} must contain a JSON object")
    return payload


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


@app.command(name="manifest")
def manifest(
    source_commit: str = typer.Option(..., min=7),
    artifacts: list[Path] = typer.Option([], exists=True, readable=True),
    kinds: list[Literal["code", "dataset", "config", "result", "manuscript", "environment", "other"]] = typer.Option([]),
    licenses: list[str | None] = typer.Option([]),
    output: Path = typer.Option(...),
    environment_lock: str = typer.Option("pyproject.toml"),
) -> None:
    if len(kinds) != len(artifacts):
        raise typer.BadParameter("--kinds count must equal --artifacts count")
    if licenses and len(licenses) != len(artifacts):
        raise typer.BadParameter("--licenses count must equal --artifacts count")
    entries = []
    for index, path in enumerate(artifacts):
        entries.append(build_artifact_entry(path, kinds[index], f"artifact-{index:03d}", licenses[index] if licenses else None))
    package = build_reproducibility_package(source_commit, entries, environment_lock, ["agentic-research-autonomous run", "agentic-research-evaluation report"], notes=["Verify all external datasets and third-party components before redistribution."])
    _write(output, package.model_dump(mode="json"))


@app.command(name="audit-license")
def audit_license(manifest_file: Path = typer.Option(..., exists=True, readable=True), output: Path = typer.Option(...)) -> None:
    payload = _read(manifest_file)
    from agentic_research.schemas.phase10 import ReproducibilityPackage
    package = ReproducibilityPackage.model_validate(payload)
    _write(output, [item.model_dump(mode="json") for item in audit_licenses(package.artifacts)])


@app.command(name="write-manuscripts")
def write_manuscripts(
    source_commit: str = typer.Option(..., min=7),
    architecture: Path = typer.Option(..., exists=True, readable=True),
    evaluation: Path = typer.Option(..., exists=True, readable=True),
    case_study: Path = typer.Option(..., exists=True, readable=True),
    output_dir: Path = typer.Option(...),
) -> None:
    system = build_system_paper(source_commit, _read(architecture))
    from agentic_research.publication.engine import build_benchmark_paper
    benchmark = build_benchmark_paper(_read(evaluation))
    case = build_case_study(_read(case_study))
    output_dir.mkdir(parents=True, exist_ok=True)
    for manuscript in (system, benchmark, case):
        md = f"# {manuscript.title}\n\n## Abstract\n{manuscript.abstract}\n\n" + "\n\n".join(f"## {section.title}\n{section.markdown}" for section in manuscript.sections)
        (output_dir / f"{manuscript.kind}.md").write_text(md, encoding="utf-8")
        (output_dir / f"{manuscript.kind}.json").write_text(manuscript.model_dump_json(indent=2), encoding="utf-8")


@app.command(name="bundle")
def bundle(
    source_commit: str = typer.Option(..., min=7),
    architecture: Path = typer.Option(..., exists=True, readable=True),
    evaluation: Path = typer.Option(..., exists=True, readable=True),
    case_study: Path = typer.Option(..., exists=True, readable=True),
    disclosure: Path = typer.Option(..., exists=True, readable=True),
    reproducibility: Path = typer.Option(..., exists=True, readable=True),
    output: Path = typer.Option(...),
) -> None:
    from agentic_research.schemas.phase10 import ReproducibilityPackage
    disclosures = json.loads(disclosure.read_text(encoding="utf-8"))
    if not isinstance(disclosures, list):
        raise typer.BadParameter("Disclosure file must contain a JSON array")
    disclosure_models = [ModelProviderDisclosure.model_validate(item) for item in disclosures]
    package = ReproducibilityPackage.model_validate_json(reproducibility.read_text(encoding="utf-8"))
    result = build_publication_bundle(source_commit, _read(architecture), _read(evaluation), _read(case_study), disclosure_models, package)
    _write(output, result.model_dump(mode="json"))
    typer.echo(f"Publication bundle {result.bundle_id} status={result.status}")


if __name__ == "__main__":
    app()
