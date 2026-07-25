"""Read-only preflight for the Ab2gA-short-v1 frozen preregistration."""

from __future__ import annotations

from pathlib import Path

from build_ab2ga_short_v1_preregistration import write_or_check


if __name__ == "__main__":
    write_or_check(Path(__file__).resolve().parents[1], check=True)
    print("ab2ga_short_v1_preregistration_preflight: OK")
