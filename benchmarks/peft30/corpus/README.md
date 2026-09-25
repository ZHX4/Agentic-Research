# Corpus (frozen artifacts live here after collection)

Status: **NOT YET FROZEN** — directory is empty by design.

After running `scripts/COLLECTION.md`:

- Store PDFs / HTML under `corpus/` with stable filenames.
- Record `local_path` + `sha256` per paper in `manifest.json`.
- Never edit a frozen file in place; a correction requires a new
  benchmark version (`sci-bench-peft30-v2`).
