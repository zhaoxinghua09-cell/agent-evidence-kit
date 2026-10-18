# Predicate: ACS conformance verdict evidence, version 1.0.0-draft

Predicate type URI (proposed, pending acceptance):
`https://github.com/GenAI-Security-Project/agent-control-standard/blob/main/docs/predicates/acs-verdict-evidence-v1.md`

Status: proposed draft `v1.0.0-draft`. Modeled on the
[agent-change-admission-v1](https://github.com/probityai/agent-evidence-vocabulary/blob/main/docs/predicates/agent-change-admission-v1.md)
predicate: same DSSE v1 envelope, same field table, same verification-step
layout, same versioning rule. This draft records the field list after the
sharpening on issue #33 (2026-10-17); it is not normative until accepted.

## Purpose

A conformance suite executes a named vector against a deployment and records
one verdict about one ACS-Core requirement: did the observed behavior match
the expected disposition for that requirement, and how independently was that
claim witnessed. This predicate packages that verdict so that a consumer of
the requirement ledger can tell, from bytes alone, (a) which vector and which
clause the verdict is about, (b) what was expected and observed, (c) whether
the witness is the deployment itself or someone who can check the requirement
without the enforcement point's own account, and (d) how much of the record
integrity covers versus what the runner's own signature covers.

A rejection is recorded with the same weight as a pass. A vector that cannot
yet be scored is quarantined, not silently defaulted.

## Envelope

The verdict is signed as a DSSE v1 envelope. The signature covers the DSSE
pre-authentication encoding of the payload type and the payload bytes, never
the raw payload:

```text
"DSSEv1" SP LEN(payloadType) SP payloadType SP LEN(payload) SP payload
```

The carriage is in-toto Statement v1, `payloadType`
`application/vnd.in-toto+json`: the statement's `_type` is
`https://in-toto.io/Statement/v1`, its `subject` is the digest-named vector,
`predicateType` is the URI above, and the verdict object is the statement's
`predicate`.

A signature's `keyid` is the lowercase hex SHA-256 of the raw public key. A
consumer pins its trusted keys out of band; a key carried inside the envelope
is never trusted. A signature naming a key the consumer did not pin is
ignored, so an envelope may carry a co-signature the consumer does not know.

## Fields

Every field below is required in a verdict record. A verifier checks them in
this order and names the first one that is absent or malformed.

| Field | Type | Meaning |
| --- | --- | --- |
| `vector_id` | 16 lowercase hex | First 16 chars of the SHA-256 of the vector input's canonical form |
| `profile` | non-empty string | ACS profile the clause belongs to (e.g. `acs-core`) |
| `anchor` | non-empty string | Repo-relative, resolvable anchor to the normative clause (a heading anchor, not bold text) |
| `clause` | non-empty string | Human-readable clause name, matching the anchor |
| `verdict` | one of `pass`, `rejected`, `unmeasurable`, `quarantined` | The four-state verdict; `quarantined` uses the quarantine record below |
| `witness_derivation.runner.id` | non-empty string | Runner identifier |
| `witness_derivation.runner.hosting_operator_id` | non-empty string | Comparable identifier of the operator who runs the runner |
| `witness_derivation.deployment_operator_id` | non-empty string | Comparable identifier of the operator of the deployment under test |
| `witness_scope` | one of `SELF`, `PEER`, `EXTERNAL` | Derived per the table below; never asserted independently |
| `verification_basis` | non-empty array of strings | Values from the registry: `wire_transcript`, `signed_decision_record`, `policy_state`, `terminal_state_evidence`, `anchor_commitment` |
| `expected` | object | Expected disposition and reason codes |
| `observed` | object | Observed disposition and reason codes |
| `behavior_snapshot` | object or `null` | Runner-captured run data (rolling chain hashes, runner id); may be `null` in an offline deterministic sample |
| `integrity.payload_digest` | 64 lowercase hex | SHA-256 of the canonical bytes of exactly the fields named in `integrity.payload_digest_fields` |
| `integrity.payload_digest_fields` | non-empty array | The names of the fields the digest covers |
| `integrity.does_not_cover` | array | Lists `behavior_snapshot`, `integrity`, `provenance`, `subject` |
| `integrity.binding` | non-empty string | States the binding consequences: observed hashes are bound only by the runner's own envelope signature; the subject is bound by the envelope, not by `payload_digest` |
| `provenance.counter_signature` | object or `null` | `null` when absent; otherwise `keyid` (lowercase hex), `lift_state` (`peer` or `co-signature`), `checked` (the requirement the key independently checked), `signer_relationship` (`peer` or `external`) |
| `provenance.anchor` | object or `null` | Persistence only: `{kind: "rfc3161-timestamp" \| "transparency-log", reference}`; never lifts `witness_scope` |

A record may carry further fields (e.g. `observed_at` RFC 3339 timestamps); a
verifier ignores fields it does not check.

## Deriving `witness_scope`

`witness_scope` is computed by the consumer, not asserted by the runner. SELF
falls out of identifier equality; only a counter-signature can lift it, and
only when it clears the registry's test: the signer can check the requirement
without relying on the enforcement point's own account.

| `hosting_operator_id == deployment_operator_id` | `provenance.counter_signature` | derived `witness_scope` |
| --- | --- | --- |
| equal | absent | `SELF` |
| equal | `lift_state: co-signature` | `SELF` (non-repudiation only; the signer did not independently check the requirement) |
| unequal | absent | not a valid `SELF` record: the runner is neither the deployment's own operator nor an independently checking witness, so the record is rejected at verification step 9 |
| any | `lift_state: peer`, `signer_relationship: peer` | `PEER` |
| any | `lift_state: peer`, `signer_relationship: external` | `EXTERNAL` |

`provenance.anchor` never appears in this table. A timestamp or a
transparency-log entry proves the digest existed at a time and was not
backdated; it is persistence, not verification. A `SELF` record carrying an
anchor remains `SELF`.

## `payload_digest` scope

`payload_digest` is SHA-256 of the canonical JSON (keys sorted, no whitespace,
UTF-8) of exactly the fields listed in `integrity.payload_digest_fields` — in
the draft sample: `anchor`, `clause`, `expected`, `observed`, `profile`,
`vector_id`, `verdict`, `verification_basis`, `witness_derivation`,
`witness_scope`. It proves those bytes are intact.

It deliberately does **not** cover:

- `behavior_snapshot` — observed run data is bound only by the runner's own
  DSSE envelope signature; a reader is told this by `integrity.binding` so
  the digest is not mistaken for a binding of the observed hashes.
- `integrity` and `provenance` themselves (self-reference).
- `subject` — the record is tied to the vector by the envelope's subject
  digest, not by `payload_digest`.

## Quarantine record

When `verdict` is `quarantined`, a second Statement carries:

| Field | Meaning |
| --- | --- |
| `quarantine_ref` | URL of the open spec issue whose closure resolves the vector's uncertainty, or `null` when no such issue exists yet |
| `quarantine_gap` | When `quarantine_ref` is `null`, the normative gap this vector's uncertainty is evidence of |
| `owner` | The accountable party (originator until the spec workstream takes the gap) |
| `review_by` | ISO date by which the gap must be resolved or the vector re-triaged; follows the `review_by` precedent on proposed terms |
| `excluded_from` | States the vector is excluded from formal results until the gap resolves |

## Verification

A verifier takes the envelope, a policy (payload type, predicate type, trusted
keys, required verification bases) and any stored transcripts it holds. It
returns `supported`, `contradicted` or `not_established`, with the reason code
of the first check that fails.

| Step | Check | Decision and reason |
| --- | --- | --- |
| 1 | The bytes parse as a DSSE envelope with payload type, base64 payload and at least one signature | no verdict, `malformed_envelope` |
| 2 | Payload type is `application/vnd.in-toto+json` | `not_established`, `unsupported_payload_type` |
| 3 | A signature naming a pinned keyid verifies | `contradicted`, `untrusted_key` / `signature_invalid` |
| 4 | The payload is an in-toto Statement v1 | `not_established`, `payload_not_statement` |
| 5 | `predicateType` is this URI | `not_established`, `unsupported_predicate` |
| 6 | Every field in the table is well formed, in table order | `not_established`, `field_invalid:<field>` |
| 7 | A subject carries `digest.sha256` equal to the canonical vector input | `contradicted`, `subject_digest_mismatch` |
| 8 | `payload_digest` recomputed over `payload_digest_fields` equals the claim | `contradicted`, `payload_digest_mismatch` |
| 9 | `witness_scope` equals the value derived from the ID equality and the counter-signature table | `contradicted`, `witness_scope_misderived` |
| 10 | A `quarantined` record carries `quarantine_ref` or `quarantine_gap`, `owner`, `review_by` | `not_established`, `quarantine_field_missing:<field>` |

A record that passes every step is `supported`. A verifier that also holds the
vector input and the wire transcript may re-execute the vector and compare its
own outcome with the signed verdict; such a recomputation adds to these steps
and never replaces one.

## What a valid record does not establish

A supported verdict means the pinned key signed exactly these bytes and the
declared digest fields recompute. It does not establish that the evaluations
ran, that the observed hashes are true, that a co-signature holder is honest,
or that a timestamp proves independence. What the verifier recomputed from
bytes and what it accepted on a signer's signature are separate statements,
and a verifier reports them separately.

## Versioning

This document is `v1.0.0-draft`; on acceptance it becomes `v1.0.0` at the URI
above. A change that adds an optional field or a reason code that refuses
nothing previously supported edits this page. A change that adds a required
field, renames a field, changes a field's type, or supports a verdict version
1 refuses is breaking: it is published as `acs-verdict-evidence-v2.md` at a
new path, and this page stays.
