
@T-n-Nelson — thank you for the confirmation and for sharpening the requirement. The point that a version label alone does not establish that the receiver held the latest applicable state is what the additions below are built around. They are proposed as record-schema fields only: the four prospective cases and their expected observations are unchanged.

## 1. Proposed receiver-visible evidence fields

Each field carries an explicit producer and a single observation point. Nothing here changes what the protocol expects to happen; it changes only what the record can show afterwards.

**Scope of this set, stated plainly:** `source_state_at_dispatch` and `receiver_state_used` are the two your requirement points to. `applicability`, `acknowledgement` and `effect_readback` are my additions to the same record, offered for you to cut rather than to accept as a set.

| Field | Content | Producer | Observation point | Value domain |
|---|---|---|---|---|
| `source_state_at_dispatch` | artefact digest + state version of the source material at the moment the amendment leaves the source | source-side producer, at dispatch | source-side dispatch record | `{digest, version, produced_by, produced_at}` |
| `receiver_state_used` | the state the receiver actually acted on, **with how it was established** | receiver, at action time | receiver-side execution record | `{version, established_by, digest?}`; `established_by` ∈ `content-digest` / `label-only` / `unstated`; `digest` is required for this field to answer the question when `established_by` = `content-digest`, and a record without it is admitted and marked incomplete on this question — a condition on the record, not an obligation on the receiver to perform a content-level comparison |
| `applicability` | whether the amendment applies to the queued action | receiver, before acting | receiver-side decision record | `{state: applicable or not-applicable, basis}` |
| `acknowledgement` | whether an acknowledgement was observed | observer designated at that observation point | observation window | `observed` / `{state: not-observed or not-evaluated, observer, coverage, window}` |
| `effect_readback` | whether the effect was independently read back | independent observer | observation window | `{state: observed, value}` / `{state: not-observed or not-evaluated, observer, coverage, window}` |

`effect_readback` is an independent readback, as your case 4 comparison states. `acknowledgement` is recorded by the observer designated at that observation point; no independence is claimed for it, and the producer column does not extend that requirement to it. Case 4 remains as you set it: acknowledgement present, independent effect readback missing.

**The load-bearing point is `established_by`.** If the receiver recorded only a label, the field reads `label-only`, and the record then explicitly does **not** support the claim "the receiver held the latest applicable state". Within this value domain, only `content-digest` supports that claim, because only a content-level identity distinguishes "the same version string" from "the same state". This is the difference between the two failure modes we are trying to keep apart: an amendment that never arrived, and an amendment that arrived but was not the state acted on. Whether an amendment ever arrived is a separate question and is not settled by this field.

**One record shape needs a stated reading rule.** If `established_by` reads `content-digest` and no digest value accompanies it, the record is admitted rather than rejected at ingest, and it is incomplete on this question — it neither supports nor refutes the claim, and it should go to review rather than be scored. Reading it as support assumes a comparison that the record does not show; reading it as non-support reports a failure that may not have occurred. This is a rule for reading such a record. It is not a new case, it is not a fourth observation value, and it does not change the expected observations of the four cases.

## 2. Why the two negative values stay separate

`no acknowledgement observed` and `no effect readback` are different facts about different fields; `not evaluated` is a different fact about the observation itself. In the schema those three facts reduce to two negative values, `not-observed` and `not-evaluated`, applied per field, and they stay separate because they are bounded by different things:

- **`not-observed`** means the observation window was open, the observer was in position, and nothing was recorded.
- **`not-evaluated`** means no observation was attempted or the coverage did not extend to that point.
- Collapsing either into the other would let a coverage gap read as a clean negative, which is exactly the confusion case 4 keeps visible.

For case 4 we keep the exact contrast you set: **acknowledgement is present, while independent effect readback is missing**. The field additions record that contrast; they do not soften, merge or reassign it.

Every `not-observed` / `not-evaluated` value therefore carries `observer`, `coverage` and `window`, so the record states what was looked at, from where, and for how long. These are the definitions we would use; if the protocol already fixes them differently, yours govern.

## 3. What this does not do

- It does not add a fifth case, and it does not change the expected observations of the existing four.
- It does not assert that a receiver must obtain content-level state identity; it makes the distinction recordable, so a review can tell which one occurred.
- It is confined to the four cases in this thread and does not extend to any receiving-side observation discussed elsewhere.
- It does not propose a schema version bump until you have reviewed the field set.

## 4. Next step

If the field set is acceptable in shape, we can turn it into a **field-level diff to the H1 text under review** — no change to the protocol's decision logic — so that the executable mapping/oracle can then be prepared and frozen against a stable document. If any field is redundant with something already in the H1 attachment, say which and we will drop it rather than keep two spellings of the same fact.

Best regards,
Xinghua Zhao — individual expert, China
