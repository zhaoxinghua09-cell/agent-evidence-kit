"""ACS conformance-verdict evidence generator (deterministic, offline).

Generates the two evidence records carried by this demo — a rejected
negative conformance vector and a quarantined spec-undecided vector —
plus their canonical-JSON SHA-256 digests. Same input bytes produce the
same digests on any machine; no network access, no third-party dependency.

生成确定性的 ACS 符合性裁决证据：一个被拒绝的负向向量，以及一个因规范未定而被隔离的
向量，二者均附带规范 JSON 的 SHA-256 摘要。同一输入字节在任何机器上产生相同摘要，
纯标准库、离线可复现。

CLI / 命令行
    python src/acs_verdict.py            run self-check, write reports/
    python src/acs_verdict.py --reports-dir DIR

Canonical rule (unchanged from the v3 demo):
    json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        .encode("utf-8")  ->  sha256
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:  # imported as part of the src package
    from . import report_html
except ImportError:  # executed as a plain script: src/ is already on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import report_html


# ---------------------------------------------------------------------------
# canonical form and digest
# ---------------------------------------------------------------------------

def canonical(o: dict) -> bytes:
    """Canonical JSON bytes: sorted keys, compact separators, UTF-8."""
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_of(o: dict) -> str:
    """SHA-256 hex digest of the canonical form of ``o``."""
    return hashlib.sha256(canonical(o)).hexdigest()


# ---------------------------------------------------------------------------
# the two wire vectors
# ---------------------------------------------------------------------------

def _negative_vector_input() -> dict:
    """Vector 1: negative conformance vector (missing request_id -> replay risk)."""
    return {
        "jsonrpc": "2.0",
        "method": "steps/toolCallRequest",
        "id": 1,
        "params": {
            "acs_version": "0.1.0",
            # request_id deliberately absent
            "timestamp": "2026-10-17T00:00:00Z",
            "metadata": {"agent_id": "dev-agent", "session_id": "sess-1", "turn_id": "t1"},
            "payload": {
                "tool": {"id": "fs.write", "capability": "write"},
                "arguments": [{"name": "path", "value": "/tmp/out"}],
                "agent_reasoning": "write output",
            },
        },
    }


def _quarantine_vector_input() -> dict:
    """Vector 2: spec-undecided field (MODIFY redaction; composition gap TBD)."""
    return {
        "jsonrpc": "2.0",
        "method": "steps/userMessage",
        "id": 2,
        "params": {
            "acs_version": "0.1.0",
            "request_id": "uuid-0002",
            "timestamp": "2026-10-17T00:00:01Z",
            "metadata": {"agent_id": "dev-agent", "session_id": "sess-1", "turn_id": "t1"},
            "payload": {"content": "PII: card 4111-1111-1111-1111", "modify": {"redact": ["card"]}},
        },
    }


# Fields payload_digest covers (integrity, not provenance).
DIGEST_FIELDS = [
    "anchor", "clause", "expected", "observed", "profile", "vector_id",
    "verdict", "verification_basis", "witness_derivation", "witness_scope",
]

PREDICATE_TYPE = (
    "https://github.com/GenAI-Security-Project/agent-control-standard/blob/main/"
    "docs/predicates/acs-verdict-evidence-v1.md"
)

WITNESS_SCOPE_DERIVATION = "hosting_operator_id == deployment_operator_id -> SELF"


# ---------------------------------------------------------------------------
# evidence statements
# ---------------------------------------------------------------------------

def build_verdict_statement() -> dict:
    """Full in-toto Statement for the rejected negative vector."""
    negative_input = _negative_vector_input()
    input_digest = digest_of(negative_input)

    # Fields payload_digest covers (integrity, not provenance).
    predicate_facts = {
        "vector_id": input_digest[:16],
        "profile": "acs-core",
        "anchor": "docs/spec/instrument/specification.md#103-replay-protection",
        "clause": "§10.3 Replay protection (ACS-Core)",
        "verdict": "rejected",
        # comparable identifiers: SELF falls out of hosting_operator_id == deployment_operator_id
        "witness_derivation": {
            "runner": {
                "id": "acs-runner@0.1.0-demo",
                "hosting_operator_id": "acme-demo:operator/deployment-01",
            },
            "deployment_operator_id": "acme-demo:operator/deployment-01",
        },
        "witness_scope": "SELF",
        "verification_basis": ["wire_transcript"],
        "expected": {"decision": "deny", "reason_codes": ["missing_request_id"]},
        "observed": {"decision": "deny", "reason_codes": ["missing_request_id"]},
    }

    payload_digest = digest_of(predicate_facts)

    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": "acs-conformance-vector:" + input_digest[:16], "digest": {"sha256": input_digest}}
        ],
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            **predicate_facts,
            "behavior_snapshot": {
                "chain_hash_before": None,
                "chain_hash_after": None,
                "runner": "acs-runner@0.1.0-demo",
                "note": "offline deterministic demo: the runner populates the section 8 rolling chain hashes from the live on-wire responses; none were produced here",
            },
            "integrity": {
                "payload_digest": payload_digest,
                "payload_digest_method": "sha256 over canonical JSON (sorted keys, compact separators, UTF-8)",
                "payload_digest_fields": DIGEST_FIELDS,
                "does_not_cover": ["behavior_snapshot", "integrity", "provenance", "subject"],
                "binding": "observed hashes are bound only by the runner's own DSSE envelope signature; the subject (vector) is bound by the envelope, not by payload_digest",
                "statement": "integrity only: proves the record is intact; not provenance",
            },
            "provenance": {
                "counter_signature": None,
                "anchor": None,
                "note": "counter_signature is the only scope lift: lift_state=peer when the pinned key independently checked this requirement (drove its own client against this deployment, or holds the wire transcript and the vector), signer_relationship=peer -> PEER / external -> EXTERNAL; otherwise lift_state=co-signature (non-repudiation only, no lift). anchor (RFC 3161 timestamp or transparency log) proves persistence, not verification; a SELF record carrying one remains SELF.",
            },
        },
    }


def build_quarantine_statement() -> dict:
    """Full in-toto Statement for the spec-undecided quarantined vector."""
    quarantine_input = _quarantine_vector_input()
    quarantine_digest = digest_of(quarantine_input)

    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": "acs-conformance-vector:" + quarantine_digest[:16], "digest": {"sha256": quarantine_digest}}
        ],
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "vector_id": quarantine_digest[:16],
            "status": "quarantined",
            "reason": "payload carries a MODIFY redaction request; how an invalid MODIFY composition fails closed (§6.3 wire semantics) is not normatively specified, so this vector cannot be scored",
            "quarantine_ref": None,
            "quarantine_gap": "Normative disposition for an unscoreable MODIFY composition. Distinct from #270, which asks what implementations must do at hooks where DENY is not a legal disposition. No open issue names this gap; this quarantined vector is the evidence it should be filed.",
            "owner": "originator (accountability transfers to the spec workstream when the gap issue is filed)",
            "review_by": "2026-11-16",
            "excluded_from": "formal result until the gap is normatively resolved",
        },
    }


def generate_evidence() -> dict:
    """Assemble the complete evidence bundle (machine-readable JSON form)."""
    verdict = build_verdict_statement()
    quarantine = build_quarantine_statement()

    return {
        "verdict": verdict,
        "quarantine": quarantine,
        "digests": {
            "negative_vector_input": verdict["subject"][0]["digest"]["sha256"],
            "quarantine_vector_input": quarantine["subject"][0]["digest"]["sha256"],
            "verdict_payload": verdict["predicate"]["integrity"]["payload_digest"],
        },
        "witness_scope_derivation": WITNESS_SCOPE_DERIVATION,
    }


# ---------------------------------------------------------------------------
# human-readable HTML report
# ---------------------------------------------------------------------------

def render_html(evidence: dict) -> str:
    """Single-page offline HTML report for the evidence bundle."""
    v = evidence["verdict"]["predicate"]
    q = evidence["quarantine"]["predicate"]
    digests = evidence["digests"]

    body = [
        "<p>"
        '<span class="badge rejected">verdict: %s</span> '
        '<span class="badge quarantined">quarantined: %s</span>'
        "</p>" % (report_html.esc(v["verdict"]), report_html.esc(q["status"])),

        report_html.html_h2("1. Verdict statement — negative conformance vector"),
        report_html.html_p(
            "A tool-call request that omits request_id; the runner denied it for "
            "replay-risk reasons. Witness scope: %s." % report_html.esc(v["witness_scope"])
        ),
        report_html.table(
            ["Field", "Value"],
            [
                ["vector_id", v["vector_id"]],
                ["profile", v["profile"]],
                ["clause", v["clause"]],
                ["expected", json.dumps(v["expected"], ensure_ascii=False)],
                ["observed", json.dumps(v["observed"], ensure_ascii=False)],
                ["witness_scope", v["witness_scope"]],
                ["verification_basis", ", ".join(v["verification_basis"])],
                ["payload_digest", digests["verdict_payload"]],
            ],
        ),
        report_html.html_p("integrity.binding: " + v["integrity"]["binding"]),

        report_html.html_h2("2. Quarantine statement — spec-undecided MODIFY composition"),
        report_html.table(
            ["Field", "Value"],
            [
                ["vector_id", q["vector_id"]],
                ["status", q["status"]],
                ["reason", q["reason"]],
                ["quarantine_ref", q["quarantine_ref"]],
                ["quarantine_gap", q["quarantine_gap"]],
                ["owner", q["owner"]],
                ["review_by", q["review_by"]],
                ["excluded_from", q["excluded_from"]],
            ],
        ),

        report_html.html_h2("3. Digests"),
        report_html.html_p("witness_scope_derivation: " + evidence["witness_scope_derivation"]),
        report_html.table(
            ["Item", "SHA-256"],
            [
                ["negative vector input_digest", digests["negative_vector_input"]],
                ["quarantine vector digest", digests["quarantine_vector_input"]],
                ["verdict payload_digest", digests["verdict_payload"]],
            ],
        ),
        report_html.html_p(
            "Deterministic: re-running yields identical digests (canonical JSON rule)."
        ),
    ]
    return report_html.html_page("ACS Verdict Evidence", body)


# ---------------------------------------------------------------------------
# self-check and CLI
# ---------------------------------------------------------------------------

EXPECTED_DIGESTS = {
    "negative_vector_input": "70cbcb3d7d7aa44cfcb0b319831cf4d5b77e51567dc9b40ecc32261be02bfa2a",
    "quarantine_vector_input": "01410bfff073d3835775373ec63be2418378de41aae00d5e6a508689079abb5f",
    "verdict_payload": "6954561a770fdfb969a12d8b7940de2511ce151ca1d95a6ef57b2ad7bec1e171",
}

DEFAULT_REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def _self_check(evidence: dict) -> None:
    """Assert the three canonical digests; exit(1) on any mismatch."""
    digests = evidence["digests"]
    failed = [
        (key, EXPECTED_DIGESTS[key], digests.get(key))
        for key in EXPECTED_DIGESTS
        if digests.get(key) != EXPECTED_DIGESTS[key]
    ]
    if failed:
        for key, expected, actual in failed:
            print("SELF-CHECK FAILED: %s" % key, file=sys.stderr)
            print("  expected: %s" % expected, file=sys.stderr)
            print("  actual  : %s" % actual, file=sys.stderr)
        sys.exit(1)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate ACS verdict evidence (JSON + HTML) after a deterministic self-check."
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help="directory for acs-verdict-evidence.json and acs-verdict-report.html (default: repo reports/)",
    )
    args = parser.parse_args(argv)

    evidence = generate_evidence()
    _self_check(evidence)

    reports_dir = args.reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "acs-verdict-evidence.json"
    html_path = reports_dir / "acs-verdict-report.html"

    json_path.write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    html_path.write_text(render_html(evidence), encoding="utf-8")

    digests = evidence["digests"]
    print("negative vector input_digest : %s" % digests["negative_vector_input"])
    print("quarantine vector digest      : %s" % digests["quarantine_vector_input"])
    print("verdict payload_digest        : %s" % digests["verdict_payload"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
