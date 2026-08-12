# Research methodology

## Research question

Can an evidence-grounded multi-agent system discover scientifically meaningful research gaps with fewer false positives than simpler LLM/RAG baselines, and can verified gaps produce hypotheses that survive reproducible experiments?

## Scope

The first experimental domain is AI/ML research, especially LLM systems. The system must support narrower domain configurations rather than assuming that one run covers all AI literature.

## Core principles

### 1. Candidate is not discovery

A gap produced from corpus absence is only a candidate. It must pass broader retrieval and adversarial counter-search before it can be described as potentially novel.

### 2. Evidence must be traceable

Every extracted scientific claim should eventually point to a paper, section/page or experiment artifact. Free-floating summaries are not acceptable as the authoritative research state.

### 3. Search the negative space

The system should explicitly search for contradictory findings, failed methods, limitations, and terminology variants. Published positive results alone create survivorship bias.

### 4. Temporal evaluation

For historical evaluations, the system must receive a strict literature cutoff and must not access future metadata, citations, embeddings, or external search results that leak post-cutoff information.

### 5. Falsification before celebration

A hypothesis needs a predefined condition under which it would be rejected. The experiment planner should optimize for information gain rather than confirmation of the preferred idea.

### 6. Reproducibility

Every experiment records code revision, dataset manifest, environment, seed, configuration, metrics, and artifacts.

## Proposed evaluation ladder

1. Retrieval quality
2. Paper fact extraction accuracy
3. Candidate-gap precision
4. False-gap rate after adversarial verification
5. Novelty verification precision
6. Hypothesis diversity/quality
7. Experimental feasibility
8. Reproducibility
9. End-to-end validated findings per compute budget

## Baselines

- Single strong LLM prompt
- RAG + LLM
- Literature-specialized agent
- Co-Scientist-style generate/critique/rank workflow
- AI-Scientist-style experiment search
- Full Agentic-Research system

## Publication strategy

The first paper should evaluate the gap-discovery framework and benchmark. A later paper can report a concrete research finding discovered by the system after independent verification.
