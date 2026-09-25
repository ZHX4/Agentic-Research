# INTERNAL — curator eyes only, NEVER give to annotators

`peft30-v1-cases.json` and `adversarial_cases.json` in this directory
contain predictive language about Agentic-Research behavior
("predicted false disproof", "System casefolds", "Alias table has no…",
"must resolve"). They are the internal measurement specification.

Annotators receive ONLY the clean package under `annotations/`:
neutral questions (`cases.clean.json`), the guide, rubrics, evidence
index, and blank response templates. Expected labels are `null`
everywhere until adjudication completes.
