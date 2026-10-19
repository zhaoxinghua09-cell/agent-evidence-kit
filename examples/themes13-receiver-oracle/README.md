# themes#13 — receiver-visible evidence: executable instance

A runnable instance of the receiver-visible evidence field set proposed in
FG-TIDA/themes#13. It turns the field table in the draft into a machine-checked
schema and runs three records against the judgement rules, with negative
controls on every rule that can fail.

## What it checks

`parse_draft_fields()` reads two things from the field table in
`fixtures/01_field_additions.md` (a copy of the published draft body): the
field names in the first column and the Value domain text in the last column.
Two reconciliations follow:

| check | reconciles | what turns it red |
|---|---|---|
| CHK-1 | record field names, required sub-keys, value domains, observation conditions | renamed / removed field, changed record |
| CHK-1b | the Value domain column vs the values this demo accepts | any value-domain term changed in the draft |

It deliberately does **not** cover the Content / Producer / Observation point
columns or prose paragraphs. Editing those turns nothing red — a stated
boundary of text-level reconciliation, not a hidden gap.

## The three records

| case | kind | content | verdict |
|---|---|---|---|
| case 4 | real — the comparison given in themes#13 | acknowledgement observed, independent effect readback not observed; receiver recorded a version label only | NOT SUPPORTED |
| SYN-B | synthetic | same version string, different digest actually used | NOT SUPPORTED |
| SYN-C | synthetic | content identity consistent | SUPPORTED |

case 4 and SYN-B differ in the evidence state, not in the verdict: case 4
never performed a content-level comparison; SYN-B performed one and found a
mismatch. The field set exists to keep those two apart.

## Run

From this directory (or a clean clone of the repository):

```
python demo_receiver_evidence.py
```

Exit code: 0 = all checks pass; 1 = a check failed; 2 = not evaluable
(draft table could not be parsed — the reconciliation chain is broken and no
conclusion is emitted, which is the point of exit 2).

```
python demo_receiver_evidence.py --show-records   # print the three records
DEMO_DRAFT_PATH=<a modified draft copy> python demo_receiver_evidence.py   # negative control
```

Standard library only; no third-party packages, no network access at run time.
Tested on CPython 3.13.

## Negative controls

Every rule carries a control that must fail when given bad input:

- CHK-1n: eight malformed records (extra field, out-of-domain
  `established_by`, content-digest without digest, missing `version`, missing
  `produced_by`, out-of-domain `applicability`, observed without `value`,
  non-observed without observation context) — all must be rejected.
- CHK-2n: a deliberately broken implementation that collapses
  `not-observed` into `not-evaluated` must be recognised by the check
  (the check returns True on the true record and False on the broken output).
- External controls A–D modify the draft itself: rename a field, replace a
  value-domain term, add a new value, delete a bare value shadowed by
  `not-observed` — each exits 1.

C and D were added after the earlier substring matching stayed green on both;
the comparison is now bidirectional token-set equality (extra and missing both
count as drift).

## Limits, stated

- Reconciliation covers only field names + Value domain token sets. It does
  not cover prose, columns 2–4, the explanation clause after "—" in the
  `receiver_state_used` cell, the `?` on `digest`, or non-hyphenated new
  words outside the vocabulary.
- SYN-B / SYN-C are synthetic and are not evidence of any real event; only
  case 4 has a real source.
- The demo does not verify the digest algorithm itself or the reasoning chain
  beyond `established_by`.

## License

Part of agent-evidence-kit, Apache-2.0.
