# agent-evidence-kit

**Runnable reference implementations of two evidence-recording tools for agentic-AI governance: an ACS conformance verdict record (in-toto Statement v1) and an evidence-graded six-domain assessment engine. Both run offline on the Python standard library and emit machine-readable JSON evidence alongside a single-page human-readable HTML report.**

---

## English

### Motivation

Standard discussions about agent control keep asking for a *reproducible* artifact — bytes a reviewer can re-run and get the same digest. This repository packages two such implementations so the evidence records they produce can be checked locally instead of being asserted from prose.

### What is inside

| Module | What it produces | Carriage |
| --- | --- | --- |
| `src/acs_verdict.py` | Two conformance verdict records against ACS-Core clause §10.3: one **rejected** negative vector (a tool-call request missing `request_id`, replay risk) and one **quarantined** vector (a MODIFY redaction composition whose normative disposition is undecided) | in-toto Statement v1, `predicateType` `acs-verdict-evidence-v1` (draft in `docs/`) |
| `src/evidence_grader.py` | A six-domain (D1–D6) evidence-graded conclusion over a built-in sample, with four-state failure semantics and an independent authorization-validity dimension | `lgd-eval/conclusion/v1.2` JSON |

### Requirements

- Python **3.8+** (developed and tested on CPython 3.13).
- **No third-party packages.** `requirements.txt` is intentionally empty; everything imports from the standard library. No network access is required at run time.

### One-click demo

From the repository root:

```text
python run_demo.py
```

This single pass runs both modules, checks the ACS digests against locked values, and writes four files under `reports/`:

```text
== [1/2] ACS conformance verdict evidence ==
  input_digest   : 70cbcb3d7d7aa44cfcb0b319831cf4d5b77e51567dc9b40ecc32261be02bfa2a
  payload_digest : 6954561a770fdfb969a12d8b7940de2511ce151ca1d95a6ef57b2ad7bec1e171
  OK
== [2/2] LGD-Eval evidence grader ==
  verdict          : Partially evidenced（部分有据）
  overall_failure  : none
  payload_digest    : 106e64ae1534df82
  OK
== reports/ ==
  acs-verdict-evidence.json   (machine-readable verdict evidence)
  acs-verdict-report.html     (human-readable single-page report)
  evidence-grader-conclusion.json
  evidence-grader-report.html
DEMO OK — both modules produced machine JSON + human HTML.
```

Add `--selftest` to also run the grader's 15 invariant assertions:

```text
python run_demo.py --selftest
```

### Dual evidence form

Every demo run writes, for each module, the **same run** in two forms:

- **Machine-readable** (`*.json`) — parseable records carrying the digests a consumer pins on. The ACS record's `integrity.payload_digest` is SHA-256 over canonical JSON (sorted keys, compact separators, UTF-8) of exactly the fields listed in `integrity.payload_digest_fields`; it declares what it does *not* cover (`behavior_snapshot`, `integrity`, `provenance`, `subject`). Re-running reproduces these bytes exactly.
- **Human-readable** (`*.html`) — a self-contained single page with the same verdict on screen: field tables, expected vs observed, and colored badges for `rejected` / `quarantined` / failure classes. No CSS framework, no fetch.

### Running a module directly

```text
python src/acs_verdict.py                              # self-check digests + write both reports
python src/evidence_grader.py --selftest               # 15 invariant checks
python src/evidence_grader.py --demo --out r.json --html r.html
python src/evidence_grader.py --json examples/caseB1_unverifiable_issuer_scope_input.json
```

### Layout

```text
agent-evidence-kit/
├── README.md                  # this file (EN + 中文)
├── LICENSE                    # Apache-2.0
├── requirements.txt           # empty — standard library only
├── run_demo.py                # one-click entry point
├── src/
│   ├── acs_verdict.py         # ACS verdict record builder + HTML report
│   ├── evidence_grader.py     # six-domain evidence grader + HTML report
│   └── report_html.py         # shared offline HTML renderer
├── docs/
│   └── acs-verdict-evidence-v1.0.0-draft.md   # predicate field table & verification steps
├── examples/                  # worked B1/B2 grader inputs and conclusions
└── reports/                   # demo output (regenerated on every run)
```

### What a record does and does not establish

A supported ACS verdict means the pinned key signed exactly these bytes and the declared digest fields recompute. It does **not** establish that the evaluations ran, that observed hashes are true, or that a timestamp proves independence. The predicate draft (`docs/`) states this boundary explicitly, and the grader deliberately computes **no composite score**: each of the six domains is graded independently (V/S/M/L/P) with its own failure class, and the overall failure class is the worst of them.

### License

Apache-2.0. See `LICENSE`.

---

## 中文

### 动机

围绕 agent 控制标准的讨论反复要求一个**可复现**工件——评审者可以本地重跑、得到相同摘要的字节。本仓库把两个这样的实现打包在一起，使它们产出的证据记录可以本地核验，而不是仅凭文字主张。

### 仓库内容

| 模块 | 产出 | 载体 |
| --- | --- | --- |
| `src/acs_verdict.py` | 针对 ACS-Core 条款 §10.3 的两条符合性判定记录：一条 **rejected** 阴性向量（工具调用请求缺 `request_id`，重放风险）与一条 **quarantined** 向量（MODIFY 改写组合的规范处置尚未确定） | in-toto Statement v1，`predicateType` 为 `acs-verdict-evidence-v1`（草稿见 `docs/`） |
| `src/evidence_grader.py` | 对内置示例的六域（D1–D6）证据分级结论，带四态失败语义与独立的授权有效性维度 | `lgd-eval/conclusion/v1.2` JSON |

### 环境要求

- Python **3.8+**（在 CPython 3.13 上开发并测试）。
- **无第三方依赖。** `requirements.txt` 刻意留空；全部使用标准库。运行时无需联网。

### 一键 demo

在仓库根目录执行：

```text
python run_demo.py
```

单次运行即执行两个模块、校验 ACS 摘要是否落在锁定值上，并在 `reports/` 下写出四个文件：

```text
== [1/2] ACS conformance verdict evidence ==
  input_digest   : 70cbcb3d7d7aa44cfcb0b319831cf4d5b77e51567dc9b40ecc32261be02bfa2a
  payload_digest : 6954561a770fdfb969a12d8b7940de2511ce151ca1d95a6ef57b2ad7bec1e171
  OK
== [2/2] LGD-Eval evidence grader ==
  verdict          : Partially evidenced（部分有据）
  overall_failure  : none
  payload_digest    : 106e64ae1534df82
  OK
== reports/ ==
  acs-verdict-evidence.json   （机器可读判定证据）
  acs-verdict-report.html     （人可读单页报告）
  evidence-grader-conclusion.json
  evidence-grader-report.html
DEMO OK — both modules produced machine JSON + human HTML.
```

加 `--selftest` 可同时运行分级器的 15 项不变量断言：

```text
python run_demo.py --selftest
```

### 双形态证据

每次 demo 运行，对每个模块都把**同一次运行**写成两种形态：

- **机器可读**（`*.json`）：可解析记录，携带评审方固定引用的摘要。ACS 记录的 `integrity.payload_digest` 是对 `integrity.payload_digest_fields` 所列字段做规范 JSON（键排序、紧凑分隔符、UTF-8）后的 SHA-256，并显式声明它**不**覆盖 `behavior_snapshot`、`integrity`、`provenance`、`subject`。重跑可逐字节复现这些值。
- **人可读**（`*.html`）：自包含单页，把同一份判定呈现在屏幕上——字段表、期望与观测对照、`rejected` / `quarantined` / 失败类的彩色徽章。不引用任何 CSS 框架、不发起网络请求。

### 单独运行某个模块

```text
python src/acs_verdict.py                              # 自检摘要 + 写出两种报告
python src/evidence_grader.py --selftest               # 15 项不变量检查
python src/evidence_grader.py --demo --out r.json --html r.html
python src/evidence_grader.py --json examples/caseB1_unverifiable_issuer_scope_input.json
```

### 目录结构

```text
agent-evidence-kit/
├── README.md                  # 本文件（EN + 中文）
├── LICENSE                    # Apache-2.0
├── requirements.txt           # 留空——仅标准库
├── run_demo.py                # 一键入口
├── src/
│   ├── acs_verdict.py         # ACS 判定记录构建 + HTML 报告
│   ├── evidence_grader.py     # 六域证据分级器 + HTML 报告
│   └── report_html.py         # 共享离线 HTML 渲染器
├── docs/
│   └── acs-verdict-evidence-v1.0.0-draft.md   # predicate 字段表与验证步骤
├── examples/                  # B1/B2 分级器输入与结论样例
└── reports/                   # demo 输出（每次运行重新生成）
```

### 一条记录能证明什么、不能证明什么

一条被支持的 ACS 判定，意味着固定密钥签署的正是这些字节、所声明的摘要字段可重算一致；它**不**证明评估真的执行过、观测到的哈希为真、或时间戳能证明独立性。predicate 草稿（`docs/`）显式写出这条边界。分级器则刻意**不计算复合分**：六个域各自独立分级（V/S/M/L/P）、各带失败类，总体失败类取最严重者。

## Examples

- [`examples/themes13-receiver-oracle/`](examples/themes13-receiver-oracle/) — a machine-checked instance of the receiver-visible evidence field set proposed in FG-TIDA/themes#13. Run `python demo_receiver_evidence.py` in that directory; see its README for checks, negative controls and stated limits.

### 许可

Apache-2.0，见 `LICENSE`。
