#!/usr/bin/env python3
"""
check-reviewer-tiers-drift.py — 评审方档位真值层漂移检测（SO-11-v2-1 lint）

读 reviewer-tiers.yaml（机器源），校验：
  1. spec §二 markdown 表格的档位与 YAML 一致
  2. YAML 的 A/B 档位在 mira-integration-status.md 平台清单内

不一致 → exit 1 + 打印差异。

跑法：python scripts/check-reviewer-tiers-drift.py
约定（AGENTS.md）：改 reviewer-tiers.yaml 后必须跑此脚本。

无 CI 场景，靠自觉 + AGENTS.md 约束。
"""

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAML_PATH = os.path.join(REPO_ROOT, "governance", "specs", "reviewer-tiers.yaml")
SPEC_REVIEW_PROCESS = os.path.join(REPO_ROOT, "governance", "specs", "governance-review-process.md")
SPEC_MIRA_STATUS = os.path.join(REPO_ROOT, "governance", "specs", "mira-integration-status.md")


def load_yaml():
    if not os.path.exists(YAML_PATH):
        return None, f"YAML 不存在: {YAML_PATH}"
    try:
        import yaml
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f.read()), "ok"
    except Exception as e:
        return None, f"YAML 解析失败: {e}"


def parse_mira_tiers():
    """解析 mira-integration-status.md 的可达档位集合。"""
    if not os.path.exists(SPEC_MIRA_STATUS):
        return None, f"mira-integration-status 不存在: {SPEC_MIRA_STATUS}"
    try:
        with open(SPEC_MIRA_STATUS, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None, f"读 mira-integration-status 失败: {e}"

    all_tiers = set()
    for pat_name, regex in [
        ("Cloud-O", re.compile(r"\|\s*\*\*Cloud-O\s*\(Claude\)\s*\*\*\s*\|\s*([^|]+)\|", re.IGNORECASE)),
        ("GPT", re.compile(r"\|\s*\*\*GPT\s*\*\*\s*\|\s*([^|]+)\|", re.IGNORECASE)),
    ]:
        for m in regex.finditer(content):
            for t in re.split(r"[/,]", m.group(1)):
                t = t.strip().strip("*` ")
                if re.match(r"^[a-zA-Z0-9.]+$", t):
                    all_tiers.add(t.lower())
    return all_tiers, "ok"


def main():
    print("=" * 60)
    print("check-reviewer-tiers-drift（SO-11-v2-1 round2 lint）")
    print("=" * 60)

    errors = []

    # 1. 读 YAML
    yaml_data, err = load_yaml()
    if yaml_data is None:
        print(f"❌ FATAL: {err}")
        sys.exit(1)
    yaml_reviewers = yaml_data.get("reviewers", {})
    yaml_tiers = {r: info.get("tier") for r, info in yaml_reviewers.items() if isinstance(info, dict)}
    print(f"✅ YAML 加载: {len(yaml_tiers)} 评审方 = {yaml_tiers}")

    # v2-1 round2: spec §二已指针化（不复述数值），不再校验 spec markdown 档位
    # 仅校验 spec §二存在指针声明（"reviewer-tiers.yaml" 引用）
    spec_has_pointer = False
    if os.path.exists(SPEC_REVIEW_PROCESS):
        try:
            with open(SPEC_REVIEW_PROCESS, "r", encoding="utf-8") as f:
                spec_content = f.read()
            spec_has_pointer = "reviewer-tiers.yaml" in spec_content
        except Exception:
            pass
    if not spec_has_pointer:
        errors.append("spec §二 缺 reviewer-tiers.yaml 指针声明（v2-1 round2 要求纯指针）")
    else:
        print("✅ spec §二 含 YAML 指针声明")

    # 2. 比对 mira-integration-status（A/B 档位必须在平台清单）
    mira_tiers, err = parse_mira_tiers()
    if mira_tiers is None:
        print(f"⚠️  mira-integration-status 不可读（跳过平台校验）: {err}")
    else:
        print(f"✅ mira 平台清单: {len(mira_tiers)} 档")
        for r, info in yaml_reviewers.items():
            if not isinstance(info, dict):
                continue
            # A/B 走 mira（platform 名含 mira）
            platform = info.get("platform", "")
            if "mira" in platform:
                tier = info.get("tier", "").lower()
                if tier and tier not in mira_tiers:
                    errors.append(f"评审方 {r}={tier}: YAML 有但 mira 平台清单无")

    # 3. 校验 dispatchers 节点完整（v2-1 round2: hook 数据驱动依赖）
    dispatchers = yaml_data.get("dispatchers", {})
    if not isinstance(dispatchers, dict) or not dispatchers:
        errors.append("YAML 缺 dispatchers 节点（hook 调度 pattern 数据源）")
    else:
        for disp_name in ("mira", "qoder_cantus"):
            d = dispatchers.get(disp_name, {})
            if not isinstance(d, dict) or not d.get("invocation_pattern"):
                errors.append(f"YAML dispatchers.{disp_name} 缺 invocation_pattern")

    print()
    if errors:
        print(f"❌ DRIFT 检测到 {len(errors)} 处不一致:")
        for e in errors:
            print(f"  - {e}")
        print()
        print("修复: 对齐 reviewer-tiers.yaml（机器源）+ spec §二指针 + mira-integration-status.md")
        sys.exit(1)
    else:
        print("✅ 一致，无漂移")
        sys.exit(0)


if __name__ == "__main__":
    main()
