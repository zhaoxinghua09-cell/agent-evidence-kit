# Fresh-Checkout Verification Report / 干净克隆复跑验证报告

Independent verification performed on a clean copy of this repository, simulating an
outside contributor who just cloned the repo. No source files, README, or LICENSE
were modified; this file (`VERIFICATION.md`) is the only artifact added.

本报告由独立验证方撰写，模拟「外人刚 clone 下来」的干净环境实跑本 repo。
未修改任何源码 / README / LICENSE，仅新增本文件。

---

## 1. Verification date / 验证日期

- 2026-10-18 (Sunday), Asia/Shanghai (UTC+8)

## 2. Environment facts / 环境事实

| Item | Value |
|---|---|
| OS | Windows (build 22621) |
| Shell | PowerShell 5.1.22621.6345 |
| `python --version` | Python 3.13.13 |
| `python` resolution | Alias → `C:\Users\Administrator\AppData\Local\Doubao\User Data\sandbox_runtime\bases\d0ace100fdff5b2d247847aca1e3d83b\python\python.exe` |
| Other pythons on PATH | `C:\Python313\python.exe`, `...\WindowsApps\python.exe` |
| `requirements.txt` | standard-library-only demo (no third-party install needed) |

Note: the verifier's shell is the Doubao sandbox runtime; `python` is an alias to the
sandbox runtime interpreter. The demo itself imports only the Python standard library
plus the repo's own `src/` package, so no `pip install` step was required and no
repo-internal PATH dependency was observed.

注：验证方 shell 为 Doubao 沙箱运行时，`python` 是指向沙箱解释器的别名；demo
仅依赖 Python 标准库与仓库自带 `src/`，无需 `pip install`，未发现仓库内部路径依赖。

## 3. Copy path / 复制路径

- Source repo: `D:\doubao\agent-evidence-kit\`
- Fresh copy: **`D:\doubao\_verify-fresh\`** (preserved on disk for re-inspection; NOT deleted)

Command used:

```powershell
Copy-Item -Recurse D:\doubao\agent-evidence-kit D:\doubao\_verify-fresh
```

### Copied root listing / 副本根目录清单

```
.gitignore
LICENSE
README.md
requirements.txt
run_demo.py
docs\acs-verdict-evidence-v1.0.0-draft.md
examples\caseB1_unverifiable_issuer_scope_conclusion.json
examples\caseB1_unverifiable_issuer_scope_input.json
examples\caseB2_confirmed_out_of_scope_issuer_conclusion.json
examples\caseB2_confirmed_out_of_scope_issuer_input.json
reports\acs-verdict-evidence.json
reports\acs-verdict-report.html
reports\evidence-grader-conclusion.json
reports\evidence-grader-report.html
src\__init__.py
src\acs_verdict.py
src\evidence_grader.py
src\report_html.py
```

Required entries all present: `README.md` / `LICENSE` / `run_demo.py` /
`requirements.txt` / `src/` / `docs/` / `examples/` / `reports/`.
必需条目全部在位。

## 4. Commands executed and results / 逐条命令与结果

All commands were run with working directory = `D:\doubao\_verify-fresh`.

### 4.1 Selftest

Command:

```powershell
python run_demo.py --selftest
```

Result: `$LASTEXITCODE = 0`. Full stdout:

```
== [1/2] ACS conformance verdict evidence ==
  input_digest   : 70cbcb3d7d7aa44cfcb0b319831cf4d5b77e51567dc9b40ecc32261be02bfa2a
  payload_digest : 6954561a770fdfb969a12d8b7940de2511ce151ca1d95a6ef57b2ad7bec1e171
  OK
== [2/2] LGD-Eval evidence grader ==
SELFTEST OK — 15 invariants passed（15 项不变量全部通过）
  verdict          : Partially evidenced（部分有据）
  overall_failure  : none
  payload_digest    : 106e64ae1534df82
  OK
== reports/ ==
  acs-verdict-evidence.json  (4824 bytes)
  acs-verdict-report.html  (4273 bytes)
  evidence-grader-conclusion.json  (5315 bytes)
  evidence-grader-report.html  (4207 bytes)

DEMO OK — both modules produced machine JSON + human HTML.
```

The required string `SELFTEST OK` is present. ✓

### 4.2 Normal demo (determinism run #2)

Command:

```powershell
python run_demo.py
```

Result: `$LASTEXITCODE = 0`. stdout structure identical to 4.1; final line
`DEMO OK — both modules produced machine JSON + human HTML.`

## 5. Assertion checklist / 断言清单

Executed via `D:\doubao\_verify-fresh\_verify_asserts.py` (verifier-owned script,
not part of the repo). Exit code = 0, 0 failures.

| # | Assertion | Status | Observed |
|---|---|---|---|
| 1 | `reports/acs-verdict-evidence.json` generated | PASS | 4824 bytes |
| 2 | `reports/acs-verdict-report.html` generated | PASS | 4273 bytes |
| 3 | `reports/evidence-grader-conclusion.json` generated | PASS | 5315 bytes |
| 4 | `reports/evidence-grader-report.html` generated | PASS | 4207 bytes |
| 5 | verdict subject digest == `70cbcb3d7d7aa44cfcb0b319831cf4d5b77e51567dc9b40ecc32261be02bfa2a` | PASS | exact match |
| 6 | quarantine subject digest == `01410bfff073d3835775373ec63be2418378de41aae00d5e6a508689079abb5f` | PASS | exact match |
| 7 | `predicate.integrity.payload_digest` == `6954561a770fdfb969a12d8b7940de2511ce151ca1d95a6ef57b2ad7bec1e171` | PASS | exact match |
| 8 | `acs-verdict-report.html` starts with `<!doctype html>` | PASS | — |
| 9 | `acs-verdict-report.html` ends with `</html>` | PASS | — |
| 10 | `acs-verdict-report.html` references no external `http(s)` `src`/`href` | PASS | 0 matches |
| 11 | `evidence-grader-report.html` starts with `<!doctype html>` | PASS | — |
| 12 | `evidence-grader-report.html` ends with `</html>` | PASS | — |
| 13 | `evidence-grader-report.html` references no external `http(s)` `src`/`href` | PASS | 0 matches |
| 14 | `evidence-grader-conclusion.json` parses with `json.load` | PASS | — |
| 15 | `schema` begins with `lgd-eval/conclusion` | PASS | `lgd-eval/conclusion/v1.2` |
| 16–21 | domains D1, D2, D3, D4, D5, D6 all present | PASS ×6 | — |

## 6. Determinism across two runs / 两次运行确定性

| Field | Run 1 (selftest) | Run 2 (normal) | Match |
|---|---|---|---|
| verdict subject digest | `70cbcb3d7d7aa44c…02bfa2a` | `70cbcb3d7d7aa44c…02bfa2a` | YES |
| quarantine subject digest | `01410bfff073d383…9abb5f` | `01410bfff073d383…9abb5f` | YES |
| ACS `payload_digest` | `6954561a770fdfb9…c1e171` | `6954561a770fdfb9…c1e171` | YES |
| grader `payload_digest` | `106e64ae1534df82` | `106e64ae1534df82` | YES |
| grader `timestamp` | `2026-10-18T00:03:09Z` | `2026-10-18T00:03:47Z` | differs (allowed) |

The three ACS digests and the grader `payload_digest` are byte-identical across runs;
only the wall-clock `timestamp` differs, as expected.

## 7. Final conclusion / 最终结论

**clean checkout runs end-to-end: YES.**

- `python run_demo.py --selftest` → exit 0, prints `SELFTEST OK` (15 invariants).
- `python run_demo.py` → exit 0, both modules emit machine-readable JSON + self-contained HTML.
- All three pinned digests hit exactly:
  verdict `70cbcb3d7d7aa44cfcb0b319831cf4d5b77e51567dc9b40ecc32261be02bfa2a`,
  quarantine `01410bfff073d3835775373ec63be2418378de41aae00d5e6a508689079abb5f`,
  integrity payload `6954561a770fdfb969a12d8b7940de2511ce151ca1d95a6ef57b2ad7bec1e171`.
- Output is deterministic across repeated runs.
- No failures, no exit-code anomalies, no missing files observed.

临时目录 `D:\doubao\_verify-fresh\` 已保留，未删除，供复查。
