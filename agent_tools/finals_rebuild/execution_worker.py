"""
Execution worker — Commit 4B.

This script is NEVER imported by the main pipeline process. It is only
ever invoked as a standalone subprocess:

    sys.executable -I execution_worker.py <artifact_path>

by agent_tools/finals_rebuild/execution_evaluator.py, which runs it inside
a fresh temp directory with a stripped environment, closed stdin, and a
wall-clock timeout. Running it here — inside a disposable child process,
never inside the pipeline's own process — is exactly what keeps the
pipeline's "do not import/exec the artifact in the main process" guarantee
true.

Behaviour is deliberately minimal: read the artifact file, compile it, and
exec it as if it were run as `python artifact.py`. Any exception (syntax
error, runtime error, whatever) propagates normally, which Python turns
into a non-zero exit code and a traceback on stderr — that alone is enough
for the caller to classify the run as return-code-0 "success" vs
non-zero "failure"; the caller does not need this script to do any
extra reporting.

*** NOT A SECURITY SANDBOX ***
This worker applies no restriction of its own beyond what the parent
process's subprocess launch configuration (isolated -I flag, temp cwd,
stripped env, timeout) provides. See execution_evaluator.py's module
docstring for the full caveat.
"""

from __future__ import annotations

import sys


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "execution_worker: expected exactly one argument (artifact path)",
            file=sys.stderr,
        )
        return 2

    artifact_path = sys.argv[1]
    with open(artifact_path, "r", encoding="utf-8") as fh:
        source = fh.read()

    code_obj = compile(source, artifact_path, "exec")
    exec_globals = {"__name__": "__main__", "__file__": artifact_path}
    exec(code_obj, exec_globals)  # noqa: S102 — this IS the execution worker
    return 0


if __name__ == "__main__":
    sys.exit(main())
