"""Ranking-quality evaluation (DESIGN §11).

Scores every synthetic resume against each JD with the real pipeline (real embedding model, FAISS,
scorer), orders resumes by score and compares with hand-labelled tiers using Spearman's rho.

    cd backend
    python -m eval.run           # local scoring only (no Gemini calls)
    python -m eval.run --llm     # also AI coaching (uses quota; needs GEMINI_API_KEY)

Exits non-zero if any job scores below the threshold, so it can gate scoring changes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scipy.stats import spearmanr

from app.container import build_container
from app.core.config import get_settings
from app.services.checker import JobSpec
from app.services.llm.schemas import JobRequirements

HERE = Path(__file__).parent
THRESHOLD = 0.6


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="use Gemini coaching (consumes quota)")
    args = ap.parse_args()

    settings = get_settings()
    container = build_container(settings) if args.llm else build_container(settings, llm=None)
    checker = container.checker
    resumes = {
        p.name: p.read_text(encoding="utf-8") for p in sorted((HERE / "data" / "resumes").glob("*.txt"))
    }
    expected = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))

    failures = 0
    for key, spec in expected.items():
        job = JobSpec(
            title=spec["title"],
            description=(HERE / "data" / "jobs" / f"{key}.md").read_text(encoding="utf-8"),
            requirements=JobRequirements(**spec["requirements"]),
            source="text",
            requirements_source="catalog",
        )
        scored = sorted(
            (
                (name, checker.analyze(text, job, ip="eval", use_ai=args.llm))
                for name, text in resumes.items()
            ),
            key=lambda x: x[1].score,
            reverse=True,
        )
        tier_of = {f: t for t, files in enumerate(spec["tiers"]) for f in files}
        rho = spearmanr([tier_of[n] for n, _ in scored], list(range(len(scored)))).statistic
        ok = rho >= THRESHOLD
        failures += not ok
        print(f"\n{spec['title']}  (Spearman rho = {rho:.2f}  {'PASS' if ok else 'FAIL'})")
        for rank, (name, r) in enumerate(scored, start=1):
            b = r.breakdown
            ai = f"  ai {b.ai:5.1f}" if b.ai is not None else ""
            print(
                f"  {rank:>2}. {name:<32} {r.score:5.1f} {r.verdict:<6} "
                f"sem {b.semantic:5.1f}  skills {b.skills:5.1f}  exp {b.experience:5.1f}{ai}"
            )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
