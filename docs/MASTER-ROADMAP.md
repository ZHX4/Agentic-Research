# Agentic-Research — Master Project Roadmap

> A complete roadmap for building, validating, operating, scaling, and releasing an evidence-grounded autonomous scientific research system.

## 1. Vision

Agentic-Research is intended to become a research infrastructure platform capable of supporting the scientific workflow from literature understanding to validated research opportunities, falsifiable hypotheses, reproducible experimentation, rigorous evaluation, bounded autonomous research, and publication packaging.

The system is not designed to turn an LLM into an unrestricted idea generator. Its central objective is to create a traceable research process in which important claims are connected to evidence, experiments are reproducible, uncertainty is preserved, and autonomous behavior is bounded by explicit scientific and operational safeguards.

The target workflow is:

```text
Scientific Literature
        ↓
Literature Intelligence
        ↓
Scientific Document Understanding
        ↓
Persistent Scientific World Model
        ↓
Research Opportunity Discovery
        ↓
Adversarial Novelty Verification
        ↓
Falsifiable Hypothesis Generation
        ↓
Reproducible Experiment Execution
        ↓
Rigorous Evaluation & Benchmarking
        ↓
Bounded Autonomous Research Control
        ↓
Evidence-Gated Publication Packaging
```

The ultimate success criterion is not that every stage exists in code. It is that a complete research cycle can be executed on a controlled corpus, audited, reproduced, and honestly reported from raw literature through final scientific outputs.

---

## 2. Definition of Success

The project is considered operationally successful only when all of the following are demonstrated:

- A clean environment can install the project without hidden local state.
- All production command-line entry points start successfully.
- Literature can be acquired and normalized with provenance.
- Scientific documents can be parsed into structured representations.
- Intermediate artifacts are valid, atomic, deterministic, and safely rerunnable.
- A persistent scientific world model can be constructed from validated documents.
- Retrieval returns source-linked results that can be inspected and evaluated.
- Candidate research gaps can be generated with supporting evidence.
- Candidate gaps can be challenged through adversarial novelty verification.
- Surviving opportunities can be transformed into falsifiable hypotheses.
- At least one feasible hypothesis can be converted into a real experiment specification.
- Experiments can execute under controlled resource and integrity constraints.
- Results can be evaluated using appropriate baselines, metrics, and reproducibility checks.
- The autonomous controller can persist state, resume safely, and stop when review policies require it.
- Publication bundles are blocked when required evidence, results, provenance, disclosures, or licensing information are missing.
- A complete run can be reproduced or its differences explained from recorded provenance.
- Production deployment can be operated with appropriate security, observability, and resource controls.

A successful run may produce a positive result, a negative result, or an inconclusive result. Scientific validity matters more than forcing a successful discovery.

---

## 3. Guiding Principles

### Evidence before conclusions

Important decisions must be supported by explicit evidence and provenance rather than unsupported model output.

### Candidate does not mean novel

A missing relationship, unexplored combination, or limitation detected in the literature is a research candidate until it survives adversarial verification.

### Failure should remain visible

Missing evidence, failed experiments, malformed inputs, and inconclusive results must be represented explicitly rather than hidden behind optimistic statuses.

### Reproducibility by construction

Code, data, configuration, environment information, seeds, results, and generated artifacts should be treated as versioned research objects.

### Bounded autonomy

Autonomous behavior must be constrained by iteration limits, retry limits, compute limits, checkpoints, reviewer policies, and explicit stop conditions.

### Human scientific responsibility

The system should accelerate research work without pretending to replace domain expertise, interpretation, or final scientific accountability.

### Modular contracts

Each major subsystem should communicate through explicit schemas and stable contracts so components can be tested independently and replaced without corrupting downstream assumptions.

### Fail closed

When required evidence or integrity conditions are missing, the system should prefer `blocked` or `inconclusive` over an unjustified successful state.

---

# 4. Phase 0 — Foundation

## Objective

Establish a stable engineering foundation for the complete research system.

## Major Tasks

- Define repository structure and package boundaries.
- Establish Python and dependency policies.
- Configure packaging and installation.
- Establish development tooling.
- Define canonical schemas and naming conventions.
- Establish configuration and environment-variable patterns.
- Establish artifact storage conventions.
- Create baseline unit and integration tests.
- Establish documentation and security conventions.
- Establish quality gates for formatting, linting, typing, and tests.

## Deliverables

```text
pyproject.toml
README.md
docs/
tests/
configs/
.env.example
LICENSE
CONTRIBUTING.md
SECURITY.md
CI configuration
```

## Acceptance Criteria

- Clean installation succeeds.
- Core package imports successfully.
- CLI entry points can be discovered.
- Basic tests execute.
- No secrets are committed.
- Configuration is reproducible.

---

# 5. Phase 1 — Literature Intelligence

## Objective

Create reliable scientific literature acquisition and normalization infrastructure.

## Major Tasks

### Source adapters

Support scholarly providers through explicit adapters with provider-specific rate limits and error handling.

### Transport

Implement:

- timeouts;
- retry policy;
- rate limiting;
- user-agent configuration;
- structured failures.

### Identity

Normalize:

- DOI;
- arXiv identifiers;
- source-specific IDs;
- URLs;
- titles;
- authors;
- dates.

### Deduplication

Prevent the same scientific work from appearing multiple times under different source representations.

### Full-text acquisition

Acquire legally available full text and record acquisition status and provenance for every paper.

## Deliverables

Canonical paper records containing stable identity, metadata, source information, provenance, and acquisition status.

## Risks

- provider outages;
- API changes;
- rate limiting;
- duplicate records;
- incomplete metadata;
- unavailable full text;
- copyright restrictions.

## Acceptance Criteria

A fixed query should produce a validated, reproducible corpus with source and identity information preserved.

---

# 6. Phase 2 — Scientific Document Understanding

## Objective

Transform scientific documents into structured representations that downstream reasoning can inspect.

## Major Tasks

- PDF and HTML parsing.
- Section detection.
- Text chunking.
- Table extraction.
- Figure metadata handling.
- Reference extraction.
- Citation relationships.
- Claim extraction.
- Evidence extraction.
- Method extraction.
- Dataset extraction.
- Task extraction.
- Metric extraction.
- Contribution extraction.
- Limitation extraction.
- Confidence and uncertainty preservation.

## Artifact Integrity

Intermediate artifacts must be written atomically:

```text
write temporary artifact
        ↓
validate complete output
        ↓
atomic rename
```

A failed run must never leave a corrupted final artifact in place.

## Idempotency

Running a stage again must not silently duplicate scientific records or append incompatible state to an old artifact.

Use unique run directories or explicit overwrite semantics.

## Deliverables

- parsed document objects;
- structured extraction objects;
- claims;
- evidence;
- citation structures;
- document-level provenance.

## Acceptance Criteria

- Every emitted artifact is valid according to its schema.
- Malformed inputs are reported explicitly.
- Re-running a stage does not silently duplicate outputs.
- Existing valid artifacts are preserved when a new run fails.

---

# 7. Phase 3 — Persistent Scientific World Model

## Objective

Represent scientific knowledge as persistent entities and relationships rather than isolated documents.

## Core Entities

- papers;
- methods;
- datasets;
- tasks;
- metrics;
- claims;
- evidence;
- limitations;
- concepts;
- citations.

## Relationships

Examples:

```text
Paper ──uses────────→ Method
Paper ──evaluates───→ Dataset
Paper ──addresses───→ Task
Paper ──reports─────→ Metric
Paper ──supports────→ Claim
Claim ──supported by→ Evidence
Paper ──cites───────→ Paper
```

## Retrieval

Support:

- lexical retrieval;
- dense retrieval;
- hybrid retrieval;
- optional reranking;
- temporal filters;
- metadata filters;
- provenance-aware result inspection.

## Deliverables

- persistent world-model database;
- indexes;
- retrieval interface;
- graph traversal interface;
- source-linked retrieval results.

## Acceptance Criteria

- Entity identity remains stable.
- Duplicate entities are controlled.
- Provenance remains attached to world-model facts.
- Retrieval results can be traced to source papers.

---

# 8. Phase 4 — Research Opportunity Discovery

## Objective

Identify candidate research opportunities from structured scientific knowledge.

## Discovery Strategies

### Missing combinations

Find method/dataset/task combinations that appear separately but are poorly explored together.

### Repeated limitations

Aggregate recurring limitations reported by independent studies.

### Contradictions

Identify incompatible conclusions or reported effects.

### Underexplored conditions

Detect methods evaluated under only a subset of plausible conditions.

### Cross-domain opportunities

Identify potentially useful transfers between neighboring research areas.

### Graph negative space

Identify scientifically plausible relationships absent from the current knowledge graph.

## Deliverables

Each candidate should carry:

- gap type;
- statement;
- supporting papers;
- supporting entities;
- evidence;
- confidence;
- limitations;
- provenance.

## Critical Rule

```text
candidate gap ≠ verified novelty
```

No candidate is allowed to bypass adversarial verification merely because a detector ranked it highly.

---

# 9. Phase 5 — Adversarial Novelty Verification

## Objective

Challenge promising research candidates by actively searching for evidence that they are already known, equivalent, or substantially weakened.

## Verification Procedure

For each candidate:

1. Search exact terminology.
2. Search synonyms and alternative formulations.
3. Search broader and narrower terminology.
4. Search recent publications.
5. Search neighboring research areas.
6. Inspect strong candidate matches.
7. Compare methods, datasets, tasks, and claims.
8. Search for counterexamples.
9. Apply temporal cutoffs when required.
10. Use full-text verification when the claim requires it.

## Result States

```text
candidate
weakened
survived
disproved
inconclusive
```

## Scientific Interpretation

The system may report that no conflicting prior work was found within a defined search and verification scope. It must not elevate that bounded result into an absolute claim of global novelty.

## Deliverables

A verification report containing:

- searches performed;
- evidence inspected;
- candidate matches;
- counterevidence;
- temporal coverage;
- full-text verification outcomes;
- final verification state;
- provenance.

---

# 10. Phase 6 — Hypothesis Reasoning

## Objective

Transform sufficiently supported research opportunities into diverse, falsifiable hypotheses.

## Generation

Use multiple generation strategies so that the search space is not dominated by one reasoning pattern.

## Reasoning and Refinement

Apply:

- reflection;
- criticism;
- confounder analysis;
- diversity assessment;
- clustering;
- tournament ranking;
- Pareto selection;
- bounded evolution.

## Required Hypothesis Structure

Every hypothesis should define:

- research question;
- motivation;
- proposed contribution;
- expected mechanism;
- experimental prediction;
- baseline requirements;
- falsification criteria;
- expected limitations;
- evidence supporting the hypothesis.

## Acceptance Criteria

No hypothesis enters experimental execution without an explicit falsification condition and identifiable evidence lineage.

---

# 11. Phase 7 — Scientific Experiment Execution

## Objective

Execute experiments under controlled and reproducible conditions.

## Experiment Specification

Every experiment must define:

- research question;
- independent variables;
- dependent variables;
- datasets;
- baselines;
- metrics;
- controls;
- random seeds;
- resource limits;
- expected outcomes;
- falsification rules.

## Execution Environment

Use controlled environments with appropriate:

- CPU limits;
- memory limits;
- process limits;
- timeout limits;
- network restrictions;
- filesystem isolation;
- capability restrictions.

## Integrity

Verify before execution:

- source code hash;
- dataset hash or deterministic tree hash;
- configuration fingerprint;
- environment fingerprint.

## Multi-Seed Execution

Execute multiple seeds when required by the experiment specification.

## Required Artifacts

```text
ExperimentSpec
SeedRun
ExperimentResult
ArtifactManifest
ExecutionLogs
EnvironmentFingerprint
```

## Acceptance Criteria

- Required metrics exist.
- Malformed metrics are rejected.
- Failed experiments cannot be misclassified as successful.
- Artifacts are hashed.
- Re-execution can be reproduced from recorded metadata.

---

# 12. Phase 8 — Evaluation & Benchmarking

## Objective

Determine whether an experimental result is meaningful, reproducible, and competitive under defined evaluation criteria.

## Evaluation Categories

### Retrieval

- Precision@k;
- Recall@k;
- F1@k;
- MRR;
- MAP@k;
- nDCG@k.

### Extraction

- exact match;
- field-level metrics;
- macro aggregation.

### Gap/Novelty Evaluation

- precision;
- recall;
- F1;
- confusion analysis.

### Temporal Integrity

- cutoff enforcement;
- future-data leakage detection;
- unknown-date handling.

### Human Evaluation

- multiple annotators;
- duplicate-rater detection;
- inter-rater agreement;
- explicit annotation contracts.

### Baselines

Comparisons must define metric direction explicitly:

```text
higher is better
or
lower is better
```

### Ablations

Measure the effect of removing or changing individual components.

### Cost and Compute

Track:

- wall time;
- CPU usage;
- GPU usage;
- memory;
- tokens;
- estimated cost.

## Benchmark Integrity

Train, development, and test splits must be disjoint by both case identity and input identity where appropriate.

Predictions must not contain duplicate or unknown case IDs.

## Deliverables

A deterministic composite evaluation report containing benchmark, human, baseline, ablation, cost, and reproducibility results.

---

# 13. Phase 9 — Autonomous Research Control

## Objective

Turn the deterministic research pipeline into a bounded, durable research control loop.

## Core Architecture

```text
Durable State
      +
Stage Adapters
      +
Checkpoints
      +
Artifact Integrity
      +
Reviewer Panel
      +
Bounded Iteration
      +
Stop Policies
```

## State Management

Persist:

- run identity;
- current iteration;
- current stage;
- completed artifacts;
- hashes;
- retries;
- reviewer results;
- provenance.

## Resume Semantics

On resume:

1. Load checkpoint.
2. Verify state integrity.
3. Verify artifact hashes.
4. Confirm stage identity.
5. Reuse only valid completed artifacts.
6. Continue from the latest valid state.

## Reviewers

At minimum:

### Provenance reviewer

Checks whether outputs are supported by traceable evidence and intact artifacts.

### Scientific-integrity reviewer

Checks methodological quality, evaluation integrity, and research validity.

## Critical Review

Any critical finding must trigger the configured stop policy even if its textual recommendation is `revise` instead of `reject`.

## Bounded Autonomy

Enforce:

- maximum iterations;
- retry limits;
- execution limits;
- no-progress detection;
- reviewer quorum rules;
- explicit stop conditions.

## Deliverables

- autonomous run state;
- checkpoints;
- review reports;
- provenance report;
- resumable run report;
- deterministic final summary.

---

# 14. Phase 10 — Publication & Release Packaging

## Objective

Produce publication-oriented artifacts without allowing incomplete or unsupported research to appear publication-ready.

## Outputs

### System manuscript

Documents the system architecture and methodology.

### Benchmark manuscript

Documents evaluation methodology and benchmark results.

### Discovery case study

Documents the chain from research opportunity to validated result.

### Reproducibility package

Contains:

- source commit;
- datasets;
- configurations;
- environment references;
- reproduction commands;
- artifact hashes;
- artifact sizes.

### Model/provider disclosure

Records relevant model and provider information.

### Licensing audit

Every release artifact must have explicit licensing coverage.

Unknown or missing licenses must result in review or blocking, never optimistic approval.

## Release-Time Integrity

Before a release bundle is marked ready:

1. Re-hash actual artifacts.
2. Compare against the manifest.
3. Verify artifact sizes.
4. Verify exact license coverage.
5. Verify evidence coverage.
6. Verify benchmark results exist.
7. Verify case-study evidence exists.
8. Verify disclosures exist.
9. Verify reproducibility information exists.

## Deliverables

```text
System Manuscript
Benchmark Report
Validated Discovery Case Study
Reproducibility Bundle
Disclosure Report
Licensing Audit
Publication Readiness Decision
```

---

# 15. Cross-Phase Integration

After individual phase acceptance, perform end-to-end integration.

## Required Flow

```text
Literature
   ↓
Structured Documents
   ↓
World Model
   ↓
Candidate Gaps
   ↓
Verification
   ↓
Hypotheses
   ↓
Experiments
   ↓
Evaluation
   ↓
Autonomous Control
   ↓
Publication
```

## Integration Rules

- Each phase must consume the canonical output contract of the previous stage.
- No phase should depend on hidden conversational state.
- Artifact paths and identifiers must remain stable throughout a run.
- Every important object must retain provenance.
- Status transitions must be explicit.
- Errors must be preserved rather than silently converted into success.

---

# 16. Reproducibility & Artifact Engineering

This is a project-wide concern rather than a single phase.

## Run Identity

Each research run should have a unique identifier and dedicated artifact namespace.

Recommended structure:

```text
artifacts/
└── runs/
    └── <run-id>/
        ├── run_manifest.json
        ├── literature/
        ├── intelligence/
        ├── world_model/
        ├── gaps/
        ├── verification/
        ├── hypotheses/
        ├── experiments/
        ├── evaluation/
        ├── autonomy/
        └── publication/
```

## Run Manifest

Record:

- run ID;
- creation time;
- source commit;
- pipeline version;
- configuration hash;
- environment fingerprint;
- artifact list;
- SHA-256 hashes;
- sizes;
- provenance references.

## Atomic Artifact Policy

No stage should overwrite a valid artifact with a partial or invalid output.

## Idempotency Policy

Repeated execution should either:

- create a new run namespace;
- explicitly overwrite a known artifact;
- or reuse a verified artifact without duplication.

Silent append-based duplication is prohibited for canonical scientific artifacts.

---

# 17. Testing Strategy

## Unit Tests

Test individual functions and models.

## Schema/Contract Tests

Test each boundary between phases.

## Integration Tests

Test multi-component flows such as:

```text
paper → extraction → world model → retrieval
```

## End-to-End Tests

Run the complete pipeline over a controlled corpus.

## Failure Tests

Test deliberately:

- malformed documents;
- missing full text;
- invalid metadata;
- corrupted artifacts;
- missing datasets;
- failed experiments;
- malformed metrics;
- checkpoint corruption;
- reviewer rejection;
- publication blocking.

## Reproducibility Tests

Execute equivalent runs twice and compare expected deterministic outputs and recorded provenance.

## Quality Gate

The project should require:

```text
ruff check .
ruff format --check .
mypy src tests
pytest -q
```

CI availability is useful evidence, but local and controlled execution results must also be retained for scientific validation.

---

# 18. Security & Safety

## Secrets

Never commit:

- API keys;
- passwords;
- access tokens;
- credentials;
- private URLs containing secrets.

Use environment variables or a dedicated secret manager.

## Experiment Isolation

Use least privilege and restricted execution environments.

## Autonomous Operation

Do not grant autonomous components unrestricted shell, network, filesystem, or infrastructure control.

## Data Protection

Separate:

```text
source data
processed data
generated research artifacts
secrets
```

and define retention rules for each.

---

# 19. Observability & Operations

## System Metrics

Track:

- job success rate;
- job failure rate;
- latency;
- resource utilization;
- queue depth;
- storage usage.

## Research Metrics

Track:

- papers ingested;
- documents successfully parsed;
- candidate gaps generated;
- candidates disproved;
- candidates surviving verification;
- hypotheses generated;
- experiments completed;
- experiments failed;
- evaluation outcomes;
- publication bundles blocked/ready.

## Scientific Health Metrics

Track:

- provenance completeness;
- verification failure rate;
- inconclusive rate;
- reviewer rejection rate;
- reproducibility failures;
- benchmark contamination incidents.

## Cost Controls

Track:

- LLM calls;
- embedding calls;
- provider costs;
- GPU hours;
- CPU hours;
- storage.

---

# 20. Human Roles & Responsibilities

The project can be operated by one person or a team. The following responsibilities should remain explicit.

## Research Lead

Owns:

- research direction;
- scientific standards;
- interpretation;
- final scientific claims.

## AI/ML Engineer

Owns:

- models;
- agents;
- retrieval;
- hypothesis reasoning;
- evaluation logic.

## Data/Infrastructure Engineer

Owns:

- ingestion;
- storage;
- experiment environments;
- deployment;
- observability.

## Scientific Reviewer

Owns:

- novelty assessment;
- methodological critique;
- result interpretation.

## Release Owner

Owns:

- publication package;
- reproducibility package;
- licensing;
- disclosure;
- release decision.

---

# 21. Required Resources

## Software

- Python 3.11+
- Git
- Docker
- package manager and virtual environments
- testing/static-analysis tooling

## Scientific Data

- scholarly literature providers;
- open/full-text sources where legally available;
- benchmark datasets;
- human-evaluation datasets when required.

## Model Resources

Potentially:

- LLM API access;
- embedding models;
- rerankers;
- local inference models.

## Compute

Development can begin with CPU-only infrastructure for ingestion, world-model construction, retrieval, and evaluation. Experimental requirements vary by hypothesis and model choice. The system should explicitly block experiments that exceed the available compute budget rather than fabricate execution.

---

# 22. Principal Risks and Mitigations

| Risk | Mitigation |
|---|---|
| False novelty | Adversarial retrieval, full-text verification, temporal safeguards |
| LLM hallucination | Evidence-linked outputs, schema validation, provenance |
| Dataset contamination | Split integrity, hash checks, temporal cutoffs |
| Weak experiments | Baselines, controls, falsification criteria, multi-seed execution |
| Autonomous runaway | Iteration limits, retry limits, reviewer stop policies |
| Reproducibility failure | Immutable manifests, artifact hashes, environment fingerprints |
| Artifact corruption | Atomic writes, validation before publish, checksums |
| Provider instability | Adapter isolation, retries, rate limits, graceful failure |
| Scaling cost | Budget controls, staged scale-up, cached artifacts |
| Publication overclaiming | Evidence-gated publication readiness |

---

# 23. Validation Roadmap After Implementation

Once the codebase is implemented, validation should proceed in increasing scope.

## Stage A — Offline Validation

- package installation;
- imports;
- CLIs;
- demo corpus;
- unit tests;
- static analysis.

## Stage B — Controlled Literature Run

Use approximately 20–50 papers in one narrow research domain.

Validate:

- acquisition;
- metadata;
- full-text;
- parsing;
- world model;
- retrieval;
- gap discovery.

## Stage C — Verification Run

Run adversarial novelty verification over selected candidates.

## Stage D — Hypothesis Run

Generate and rank multiple hypotheses.

## Stage E — Experimental Run

Select one feasible hypothesis and execute a real experiment.

## Stage F — Evaluation Run

Produce the benchmark/evaluation report.

## Stage G — Autonomous Run

Run one bounded autonomous cycle over the validated research state.

## Stage H — Reproducibility Run

Repeat the research run from a clean environment and compare artifacts and outputs.

## Stage I — Publication Run

Generate a publication package and confirm all release gates behave correctly.

---

# 24. Scale-Up Roadmap

Scale only after correctness has been demonstrated at the previous level.

```text
20–50 papers
      ↓
100–500 papers
      ↓
1,000–5,000 papers
      ↓
10,000+ papers
      ↓
domain-scale corpus
      ↓
cross-domain research discovery
```

At each increase, reassess:

- retrieval recall;
- deduplication quality;
- parsing throughput;
- storage;
- verification cost;
- model cost;
- false positive gap rate;
- false negative gap rate;
- experiment throughput.

Do not treat larger corpus size as automatically better research quality.

---

# 25. Deployment Roadmap

## Local Research Environment

Run the complete system locally with controlled artifacts and credentials.

## Single-Server Deployment

Introduce:

- persistent service process;
- durable storage;
- scheduled research jobs;
- centralized logs;
- secret management;
- backups.

## Scalable Deployment

When workload justifies it, separate:

```text
API / UI
   ↓
Research Controller
   ↓
Job Queue
   ├── Literature Workers
   ├── Intelligence Workers
   ├── Verification Workers
   ├── Hypothesis Workers
   ├── Experiment Workers
   └── Evaluation Workers
   ↓
Persistent Databases
   ↓
Artifact Storage
```

## Production Safeguards

- least-privilege credentials;
- isolated experiment runners;
- resource quotas;
- audit logs;
- backups;
- health checks;
- restart policies;
- alerting;
- rollback procedures.

---

# 26. Definition of Fully Operational

The system reaches the fully operational milestone only when all of the following are demonstrated on a real controlled run:

```text
[ ] clean installation
[ ] production CLI startup
[ ] offline demo
[ ] literature acquisition
[ ] corpus validation
[ ] full-text acquisition
[ ] structured document understanding
[ ] persistent world model
[ ] retrieval validation
[ ] candidate gap discovery
[ ] adversarial novelty verification
[ ] falsifiable hypothesis generation
[ ] real experiment execution
[ ] benchmark/evaluation report
[ ] autonomous control
[ ] checkpoint/resume validation
[ ] critical-review stop validation
[ ] reproducibility rerun
[ ] publication package
[ ] release integrity verification
[ ] security audit
[ ] quality gate
[ ] operational monitoring
```

Only after this gate should the system be described as a demonstrated autonomous research platform rather than an implemented research framework.

---

# 27. Final Execution Order

The recommended master execution sequence is:

```text
1. Foundation
       ↓
2. Literature Intelligence
       ↓
3. Scientific Document Understanding
       ↓
4. Scientific World Model
       ↓
5. Research Opportunity Discovery
       ↓
6. Adversarial Novelty Verification
       ↓
7. Hypothesis Reasoning
       ↓
8. Experiment Design & Execution
       ↓
9. Evaluation & Benchmarking
       ↓
10. Autonomous Research Control
       ↓
11. Publication Packaging
       ↓
12. End-to-End Integration Validation
       ↓
13. Reproducibility Rerun
       ↓
14. Security & Operational Hardening
       ↓
15. Single-Server Deployment
       ↓
16. Monitoring & Maintenance
       ↓
17. Controlled Scale-Up
       ↓
18. Cross-Domain Research Discovery
```

The implementation roadmap and the validation roadmap should remain separate in project management: having a component implemented does not prove that the complete scientific workflow has been successfully demonstrated.

---

# 28. Long-Term Research Objective

Once the operational foundation is proven, the project can pursue its deeper objective: enabling AI-assisted discovery at a scale beyond what a researcher can manually traverse.

The long-term system should be capable of:

- maintaining a continuously updated scientific world model;
- monitoring newly published research;
- revisiting previously inconclusive opportunities;
- generating competing hypotheses;
- allocating experiments under a compute budget;
- learning from failed experiments;
- comparing alternative research directions;
- maintaining long-lived research memory;
- detecting emerging scientific trends;
- supporting multiple domains;
- producing auditable research programs rather than isolated ideas.

The final target is not autonomous text generation. It is a **reproducible scientific discovery infrastructure** in which AI systems can search, reason, experiment, criticize, learn from results, and preserve the evidence required for humans to understand and trust what they find.
