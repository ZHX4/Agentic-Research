"""Phase 7 scientific execution package."""

from .planner import build_experiment_spec, build_falsification_plan
from .runner import evaluate_falsification, run_experiment
from .sandbox import DockerSandboxExecutor, SandboxViolation
from .tree import append_result, create_tree

__all__ = [
    "DockerSandboxExecutor",
    "SandboxViolation",
    "append_result",
    "build_experiment_spec",
    "build_falsification_plan",
    "create_tree",
    "evaluate_falsification",
    "run_experiment",
]
