# Provider snapshots (frozen, hash-pinned)

Status: **NOT YET FROZEN** — no live queries run here.

Each snapshot is a `ProviderSnapshot`
(`src/agentic_research/benchmarks/snapshots.py`):

- provider, query, UTC timestamp, result IDs + count,
  request params, temporal filter, payload hash.

Snapshots reproduce provider-dependent evaluation without
re-querying live services. Live results never become benchmark
truth automatically; only adjudicated labels do.
