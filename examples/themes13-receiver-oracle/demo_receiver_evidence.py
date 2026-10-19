#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demo_receiver_evidence.py — themes#13「receiver-visible evidence」字段集的**可执行实例 + 自评测**

它做三件事，且每件都能失败（R1）：

  1) 把草稿 01 的字段表**解析成机器可读的 schema**，与实例记录对账：字段名、必填子键、
     值域、观察条件，逐项落成检查。任何一边漂移 -> FAIL。
  2) 用 3 个实例记录跑判据：
       case 4    **真实**（Nelson 在 themes#13 给的对比：ack 在、independent effect readback 缺）
       SYN-B     **合成**（版本号相同但摘要不同 —— label-only 陷阱的可执行版）
       SYN-C     **合成**（内容级身份一致 —— 唯一能支撑 claim 的形状）
  3) 每条判据都配**负控**：构造应当被拒的输入，验证判据真的会拒。
     其中两条负控是「用坏实现证明检查会失败」（不是「值不相等」这种恒真断言）。

退出码：0 = 全部 OK；1 = 有 check FAIL；2 = 无法求值（NOT VERIFIED，不等于通过）

用法：
  python demo_receiver_evidence.py
  python demo_receiver_evidence.py --show-records
  DEMO_DRAFT_PATH=<改坏的草稿副本> python demo_receiver_evidence.py   # 负对照
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFT = os.environ.get("DEMO_DRAFT_PATH") or os.path.join(
    HERE, "fixtures", "01_field_additions.md")

# ---- 值域（与草稿表逐项对应；改这里必须同步改草稿，否则 CHK-1 会红） ----
DOMAIN = {
    "established_by": {"content-digest", "label-only", "unstated"},
    "applicability": {"applicable", "not-applicable"},
    "acknowledgement": {"observed", "not-observed", "not-evaluated"},
    "effect_readback": {"observed", "not-observed", "not-evaluated"},
}
OBS_CTX = ("observer", "coverage", "window")
REQUIRED_KEYS = {
    "source_state_at_dispatch": ("digest", "version", "produced_by", "produced_at"),
    "receiver_state_used": ("version", "established_by"),
    "applicability": ("state", "basis"),
}
BOOKKEEPING = {"case", "instance_kind", "note"}
# 值域键 → 承载它的字段行（established_by 是 receiver_state_used 的子键）
DOMAIN_OWNER = {"established_by": "receiver_state_used"}

# 每行 Value domain 应当出现的 token（**双向**对账：多一个、少一个都算漂移）
ROW_TOKENS = {
    "source_state_at_dispatch": {"digest", "version", "produced_by", "produced_at"},
    "receiver_state_used": {"version", "established_by", "digest",
                            "content-digest", "label-only", "unstated"},
    "applicability": {"state", "applicable", "not-applicable", "basis"},
    "acknowledgement": {"observed", "state", "not-observed", "not-evaluated",
                        "observer", "coverage", "window"},
    "effect_readback": {"observed", "state", "value", "not-observed", "not-evaluated",
                        "observer", "coverage", "window"},
}
# 只认这些词，散文（is / required / question …）一律忽略
VOCAB = set().union(*ROW_TOKENS.values())
RE_HYPH = re.compile(r"\b(?:not-)?[a-z]+(?:-[a-z]+)+\b")
RE_KEY = re.compile(r"\b(?:%s)\b" % "|".join(sorted(VOCAB, key=len, reverse=True)))


def cell_tokens(cell):
    """从 Value domain 单元格取 token 集合。

    先按「 — 」截断，丢掉解释性从句（那里面会出现 content-level 这类非 schema 词），
    再取 (a) 所有连字符词（能抓出 not-checked 这种**新增**取值）(b) 词表内的单词。"""
    head = cell.split(" — ")[0]
    got = set(RE_HYPH.findall(head)) | set(RE_KEY.findall(head))
    return got



# ---------------------------------------------------------------- 解析草稿字段表
def parse_draft_fields(path):
    """从草稿 01 的 markdown 表取字段名与「Value domain」列。返回 (fields, vd, err)。

    vd[field] = 该行最后一列的原文 —— 用于**值域对账**：草稿里写的值域必须包含
    demo 认为合法的每个取值，否则 CHK-1b 报红（防止只对字段名、不对值域）。"""
    if not os.path.isfile(path):
        return None, None, "draft not found: %s" % path
    fields, vd = [], {}
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            s = ln.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 5:
                continue
            m = re.match(r"^`([a-z_]+)`$", cells[0])
            if m:
                fields.append(m.group(1))
                vd[m.group(1)] = cells[-1]
    if not fields:
        return None, None, "no field rows parsed from draft table"
    return fields, vd, None


# ---------------------------------------------------------------- 判据
def state_of(v):
    """字段值可能是裸字符串（observed），也可能是带观察条件的对象。"""
    return v if isinstance(v, str) else (v or {}).get("state")


def claim_supported(rec):
    """记录是否支撑「receiver 持有最新的适用状态」这句话。

    返回 (supported, reason)，supported ∈ {True, False, None}。
    None = 记录不完整、不足以判定 —— 既不得读成 True，也不得读成 False。"""
    rsu = rec.get("receiver_state_used") or {}
    by = rsu.get("established_by")
    if by not in DOMAIN["established_by"]:
        # 越界或缺失：记录先要过 validate。此处不猜 False（那会把"不合规"说成"不支撑"）。
        return None, "established_by 缺失或越界（%r），记录未通过结构校验" % (by,)
    if by == "content-digest":
        a = (rec.get("source_state_at_dispatch") or {}).get("digest")
        b = rsu.get("digest")
        if not a or not b:
            return None, "established_by=content-digest 但缺 digest，记录不完整，应进复核"
        return (a == b), ("摘要相同" if a == b else "摘要不同：接收方用的不是发出时的状态")
    if by == "label-only":
        return False, "仅凭版本标签，无法区分「同版本号」与「同状态」"
    return False, "unstated：未记录如何确立，不得据此断言"


def validate(rec, allowed_fields):
    """记录结构校验。返回 errors 列表（空 = 合法）。

    覆盖草稿表里能机械化的全部约束：
      · 字段名集合 == 草稿字段表（多/少都报）
      · 每个子对象的必填键
      · established_by / applicability / 两个观察字段的值域
      · established_by=content-digest 时 digest 必须存在（**记录完整性**，不是对接收方的义务）
      · 非 observed 必须自带 observer / coverage / window
    """
    errs = []
    extra = set(rec) - set(allowed_fields) - BOOKKEEPING
    if extra:
        errs.append("未在草稿字段表中的字段: %s" % sorted(extra))
    for f in allowed_fields:
        if f not in rec:
            errs.append("缺字段: %s" % f)

    # 必填子键
    for f, keys in REQUIRED_KEYS.items():
        v = rec.get(f)
        if not isinstance(v, dict):
            if f in rec:
                errs.append("%s 必须是对象（含 %s）" % (f, "/".join(keys)))
            continue
        for k in keys:
            if not v.get(k):
                errs.append("%s 缺 %s" % (f, k))

    # established_by 值域 + digest 完整性
    rsu = rec.get("receiver_state_used") or {}
    by = rsu.get("established_by")
    if by is not None and by not in DOMAIN["established_by"]:
        errs.append("established_by 取值 %r 不在值域 %s" % (by, sorted(DOMAIN["established_by"])))
    if by == "content-digest" and not rsu.get("digest"):
        errs.append("established_by=content-digest 但缺 digest（草稿：digest 必填 → 记录不完整）")

    # applicability：{state, basis}，state 必须取值域内
    ap = rec.get("applicability")
    st = state_of(ap)
    if st is not None and st not in DOMAIN["applicability"]:
        errs.append("applicability 取值 %r 不在值域 %s" % (st, sorted(DOMAIN["applicability"])))

    # 观察类字段
    for f in ("acknowledgement", "effect_readback"):
        v = rec.get(f)
        s = state_of(v)
        if s is None:
            errs.append("%s 缺 state" % f)
            continue
        if s not in DOMAIN[f]:
            errs.append("%s 取值 %r 不在值域 %s" % (f, s, sorted(DOMAIN[f])))
        if s == "observed":
            if f == "effect_readback" and not (isinstance(v, dict) and "value" in v):
                errs.append("effect_readback=observed 必须带 value（草稿值域 {state: observed, value}）")
            if f == "acknowledgement" and not isinstance(v, str):
                errs.append("acknowledgement=observed 必须写成裸值 `observed`（草稿值域只有裸值，不带观察条件）")
        else:
            if isinstance(v, str):
                errs.append("%s=%s 缺 %s —— 不带观察条件不得报「未观察到」"
                            % (f, s, "/".join(OBS_CTX)))
            else:
                for need in OBS_CTX:
                    if need not in v:
                        errs.append("%s=%s 缺 %s（草稿 §2：不带观察条件不得报「未观察到」）"
                                    % (f, s, need))
    return errs


# ---------------------------------------------------------------- 实例
def cases():
    """3 个实例。真实/合成逐条标注，不混。"""
    return [
        {
            "case": "4",
            "instance_kind": "REAL — themes#13, Nelson 原文给出的对比",
            "note": "acknowledgement 存在，而 independent effect readback 缺失",
            "source_state_at_dispatch": {
                "digest": "dg-aa11", "version": "H1-r3",
                "produced_by": "source-side producer",
                "produced_at": "2026-10-19T08:53:19Z",
            },
            "receiver_state_used": {"version": "H1-r3", "established_by": "label-only"},
            "applicability": {"state": "applicable", "basis": "queued action predates the amendment"},
            "acknowledgement": "observed",
            "effect_readback": {
                "state": "not-observed",
                "observer": "independent observer",
                "coverage": "H1 effect readback",
                "window": "case-4 observation window",
            },
        },
        {
            "case": "SYN-B",
            "instance_kind": "SYNTHETIC — 演示用，不对应任何真实事件",
            "note": "版本号相同，但 receiver 实际执行的摘要不同 —— label-only 的典型陷阱",
            "source_state_at_dispatch": {
                "digest": "dg-aa11", "version": "H1-r3",
                "produced_by": "source-side producer",
                "produced_at": "2026-10-19T09:00:00Z",
            },
            "receiver_state_used": {
                "version": "H1-r3", "established_by": "content-digest", "digest": "dg-bb22",
            },
            "applicability": {"state": "applicable", "basis": "queued action predates the amendment"},
            "acknowledgement": "observed",
            "effect_readback": {"state": "observed", "value": "state advanced to H1-r3"},
        },
        {
            "case": "SYN-C",
            "instance_kind": "SYNTHETIC — 演示用，不对应任何真实事件",
            "note": "唯一能支撑 claim 的形状：内容级身份且与发出态一致",
            "source_state_at_dispatch": {
                "digest": "dg-aa11", "version": "H1-r3",
                "produced_by": "source-side producer",
                "produced_at": "2026-10-19T09:05:00Z",
            },
            "receiver_state_used": {
                "version": "H1-r3", "established_by": "content-digest", "digest": "dg-aa11",
            },
            "applicability": {"state": "applicable", "basis": "queued action predates the amendment"},
            "acknowledgement": "observed",
            "effect_readback": {"state": "observed", "value": "state advanced to H1-r3"},
        },
    ]


def _merged(rec):
    """**坏实现**：把 not-observed 归一化成 not-evaluated（正是草稿禁止的塌缩）。
    专门用来做负控——如果检查认不出这个坏输入，检查就是装饰品。"""
    r = json.loads(json.dumps(rec))
    for f in ("acknowledgement", "effect_readback"):
        if state_of(r.get(f)) == "not-observed":
            r[f]["state"] = "not-evaluated"
    return r


def keeps_absence_kind(rec):
    """检查：记录是否**原样保住** not-observed 这个取值（未被塌缩成 not-evaluated）。"""
    return state_of(rec.get("effect_readback")) == "not-observed"


# ---------------------------------------------------------------- 自检
def run(show_records=False):
    res = {}
    fields, vd, err = parse_draft_fields(DRAFT)
    if err:
        print("[NOT VERIFIED] 无法解析草稿字段表: %s" % err)
        print("  （草稿被改过或路径变了 —— 对账链断了就不许出结论，这是 exit 2 的意义）")
        return 2
    allowed = set(fields)
    print("[DRAFT] 草稿字段表解析出 %d 个字段: %s" % (len(fields), ", ".join(fields)))

    recs = cases()
    if show_records:
        for r in recs:
            print("\n--- %s ---\n%s" % (r["case"], json.dumps(r, ensure_ascii=False, indent=2)))

    # ---- CHK-1 结构对账：字段名 + 必填子键 + 值域 + 观察条件 ----
    errs_all = {r["case"]: validate(r, allowed) for r in recs}
    res["CHK-1 结构对账(字段名/子键/值域/观察条件)"] = all(not v for v in errs_all.values())

    # ---- CHK-1b 值域对账：草稿该行的 Value domain 与 demo 的 token 集合**双向相等** ----
    # 单向子串会漏两类：① 草稿**新增**取值（not-checked）；② 被 not-observed 遮蔽的删值（删 observed）。
    dom_gaps = []
    for f, want in ROW_TOKENS.items():
        got = cell_tokens(vd.get(f, ""))
        miss = sorted(want - got)
        extra = sorted(got - want)
        if miss:
            dom_gaps.append("%s 缺 %s" % (f, "/".join(miss)))
        if extra:
            dom_gaps.append("%s 多出 %s（草稿新增了 demo 不认的取值）" % (f, "/".join(extra)))
    res["CHK-1b 值域对账(双向：多/少都算漂移)"] = not dom_gaps

    # 负控组：每种坏输入都必须被 validate 拒
    bad = []

    b = json.loads(json.dumps(recs[2])); b["receiver_signature"] = "x"
    bad.append(("多余字段", b))

    b = json.loads(json.dumps(recs[2])); b["receiver_state_used"]["established_by"] = "assumed"
    bad.append(("established_by 越界", b))

    b = json.loads(json.dumps(recs[2])); del b["receiver_state_used"]["digest"]
    bad.append(("content-digest 无 digest", b))

    b = json.loads(json.dumps(recs[2])); del b["receiver_state_used"]["version"]
    bad.append(("缺 version", b))

    b = json.loads(json.dumps(recs[2])); del b["source_state_at_dispatch"]["produced_by"]
    bad.append(("缺 produced_by", b))

    b = json.loads(json.dumps(recs[2])); b["applicability"] = {"state": "maybe", "basis": "x"}
    bad.append(("applicability 越界", b))

    b = json.loads(json.dumps(recs[2])); b["effect_readback"] = {"state": "observed"}
    bad.append(("observed 缺 value", b))

    b = json.loads(json.dumps(recs[0]))
    for k in OBS_CTX:
        b["effect_readback"].pop(k, None)
    bad.append(("非 observed 缺观察条件", b))

    caught = [(name, bool(validate(x, allowed))) for name, x in bad]
    res["CHK-1n 负控组：%d 种坏输入全部被拒" % len(bad)] = all(ok for _, ok in caught)

    # ---- CHK-2 case 4 的对比原样保留 ----
    c4 = recs[0]
    res["CHK-2 case4 对比原样保留(ack=observed / effect=not-observed)"] = (
        state_of(c4["acknowledgement"]) == "observed" and keeps_absence_kind(c4))

    # ---- CHK-2n 负控：塌缩 not-observed -> not-evaluated 必须被检查认出来 ----
    # 这不是「值不相等」的恒真断言：检查函数对真记录返回 True，对坏实现产出的记录必须返回 False。
    res["CHK-2n 负控：塌缩 not-observed->not-evaluated 必须被认出"] = (
        keeps_absence_kind(c4) is True and keeps_absence_kind(_merged(c4)) is False)

    # ---- CHK-3 label-only 绝不得被读成「已持有最新状态」 ----
    sup_a, why_a = claim_supported(recs[0])
    res["CHK-3 label-only -> 不支撑 claim"] = (sup_a is False and "标签" in why_a)

    # ---- CHK-4 版本号相同但摘要不同 -> 必须判不支撑 ----
    sup_b, why_b = claim_supported(recs[1])
    res["CHK-4 同版本号/不同摘要 -> 不支撑"] = (sup_b is False and "摘要不同" in why_b)

    # ---- CHK-5 内容级身份一致 -> 才判支撑 ----
    sup_c, _ = claim_supported(recs[2])
    res["CHK-5 content-digest 且一致 -> 支撑"] = (sup_c is True)

    # ---- CHK-6 声明 content-digest 却无 digest -> 记录不完整且不可判定（两段都要成立）----
    rec_nodig = json.loads(json.dumps(recs[2]))
    del rec_nodig["receiver_state_used"]["digest"]
    sup_d, _ = claim_supported(rec_nodig)
    res["CHK-6 无 digest -> validate 报错 且 判定为不可判定"] = (
        bool(validate(rec_nodig, allowed)) and sup_d is None)

    ok = all(res.values())
    print("\n[EVAL]", "PASS" if ok else "FAIL")
    for k, v in res.items():
        print("  %-52s %s" % (k, "OK" if v else "**FAIL**"))
    print("\n[负控明细] 每种坏输入是否被拒：")
    for name, caught_ok in caught:
        print("  %-28s %s" % (name, "拒绝 OK" if caught_ok else "**放行 = 检查有洞**"))

    print("\n[VERDICTS]")
    for r in recs:
        s, why = claim_supported(r)
        label = {True: "SUPPORTED", False: "NOT SUPPORTED", None: "UNDECIDABLE"}[s]
        print("  %-6s %-14s ack=%-12s effect=%-13s -> %s"
              % (r["case"], label, state_of(r["acknowledgement"]),
                 state_of(r["effect_readback"]), why))

    if not ok:
        print("\n[FAIL DETAIL]")
        for k, v in errs_all.items():
            if v:
                print("  %s: %s" % (k, "; ".join(v)))
        for name, caught_ok in caught:
            if not caught_ok:
                print("  负控放行: %s" % name)
        for g in dom_gaps:
            print("  值域漂移: %s" % g)
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show-records", action="store_true")
    a = ap.parse_args()
    return run(a.show_records)


if __name__ == "__main__":
    sys.exit(main())
