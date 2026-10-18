#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-click demo for agent-evidence-kit. / 一键 demo 入口。

Runs both evidence modules from a clean checkout and, in a single pass,
writes four files under reports/:

    reports/acs-verdict-evidence.json        machine-readable verdict evidence
    reports/acs-verdict-report.html          human-readable single-page report
    reports/evidence-grader-conclusion.json  machine-readable graded conclusion
    reports/evidence-grader-report.html      human-readable single-page report

Usage / 用法:
    python run_demo.py            # run the demo
    python run_demo.py --selftest # also run the evidence-grader invariant tests

Standard library only; Python 3.8+; tested on CPython 3.13.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
REPORTS = ROOT / "reports"
sys.path.insert(0, str(SRC))


def _write(rel: str, text: str) -> Path:
    out = REPORTS / rel
    out.write_text(text, encoding="utf-8")
    return out


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    failures: list = []

    # --- Module 1: ACS conformance verdict evidence (deterministic) ---
    print("== [1/2] ACS conformance verdict evidence ==")
    try:
        import acs_verdict
        evidence = acs_verdict.generate_evidence()
        acs_verdict._self_check(evidence)  # raises on digest drift
        _write("acs-verdict-evidence.json",
               json.dumps(evidence, indent=2, ensure_ascii=False))
        _write("acs-verdict-report.html", acs_verdict.render_html(evidence))
        d = evidence["digests"]
        print("  input_digest   :", d["negative_vector_input"])
        print("  payload_digest :", d["verdict_payload"])
        print("  OK")
    except Exception as e:  # noqa: BLE001 - demo must report and continue
        failures.append("acs_verdict: %r" % e)
        print("  FAIL:", e)

    # --- Module 2: LGD-Eval evidence grader (six domains) ---
    print("== [2/2] LGD-Eval evidence grader ==")
    try:
        import evidence_grader
        if "--selftest" in sys.argv:
            rc = evidence_grader.run_selftest()
            if rc != 0:
                failures.append("evidence_grader selftest failed")
        conclusion = evidence_grader.generate_evidence()
        _write("evidence-grader-conclusion.json",
               json.dumps(conclusion, indent=2, ensure_ascii=False))
        _write("evidence-grader-report.html", evidence_grader.render_html(conclusion))
        print("  verdict          :", conclusion["verdict"])
        print("  overall_failure  :", conclusion["overall_failure_class"])
        print("  payload_digest    :", conclusion["reproducibility"]["payload_digest"])
        print("  OK")
    except Exception as e:  # noqa: BLE001
        failures.append("evidence_grader: %r" % e)
        print("  FAIL:", e)

    print("== reports/ ==")
    for p in sorted(REPORTS.iterdir()):
        if p.is_file():
            print("  %s  (%d bytes)" % (p.name, p.stat().st_size))

    if failures:
        print("\nDEMO FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nDEMO OK — both modules produced machine JSON + human HTML.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
