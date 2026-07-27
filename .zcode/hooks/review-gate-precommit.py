#!/usr/bin/env python3
"""
Pre-commit Review Gate -- PreToolUse Hook (round2)
===================================================
强制执行 governance-review-process.md §四.步骤0：ECS 改动必须先走三方评审。

round2 改动（C 第三方案 + B-Q1 补充）：
  - 闸门表 markdown → YAML，gate_id 精确等值查找（消灭子串误匹配）
  - 补 rsync + IP 直连两条无意路径（B-Q1 裁定：防忘记模型下高概率手法）
  - override 使用必须在闸门表留痕（B-Q5）
  - 失败 deny 消息列出所有 open gate_id（把"猜"的负担移给人）

机制：
  拦 Bash 命令，正则匹配"传输 apply-*.py 到 ECS / ssh 写 /opt/pi-orchestrator"，
  从命令提取 gate_id（apply-<gate_id>*.py），查 pre-commit-review-gate-log.yaml
  是否有 verdict=PASS 条目。无 PASS → exit 2 deny。

威胁模型：防忘记，不防恶意（plan §五.5 + C 裁定）。
"""

import json
import os
import re
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OVERRIDE_FILE = os.path.join(SCRIPT_DIR, ".review-gate-override.json")

# repo root 推断：hook 位于 <repo>/.zcode/hooks/，向上两级是 repo root
# 环境变量优先（测试用），否则用脚本位置推断（团队 clone 零配置）
_DEFAULT_REPO = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REPO_ROOT = os.environ.get("AGENT_COLLABORATION_REPO", _DEFAULT_REPO)
GATE_LOG = os.path.join(REPO_ROOT, "governance", "specs", "pre-commit-review-gate-log.yaml")

# ECS 主机标识：域名 + IP 直连（B-Q1 补充：domain/IP 混用是真实日常）
# 匹配 aetherisonline.xyz / aetheris-ecs.pem / 或 IP 直连（配合下文 ssh/scp 上下文）
ECS_DOMAIN_PATTERN = r"(aetherisonline\.xyz|aetheris-ecs)"
# IP 直连：仅在与 scp/ssh + apply-*.py 或 /opt/pi-orchestrator 同现时才认作 ECS
IP_PATTERN = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"

# 强制触发路径
# 1. scp/rsync apply-*.py 到 ECS（patch 脚本部署）
TRANSFER_APPLY_PATTERN = re.compile(
    rf"\b(scp|rsync)\b.*\bapply-[a-z0-9-]+\.py\b.*({ECS_DOMAIN_PATTERN}|{IP_PATTERN})",
    re.IGNORECASE,
)
# 2. ssh 操作 /opt/pi-orchestrator 写路径 或 systemctl 写操作
SSH_WRITE_PATTERN = re.compile(
    rf"\bssh\b.*({ECS_DOMAIN_PATTERN}|{IP_PATTERN}).*"
    r"(/opt/pi-orchestrator/|systemctl\s+(restart|start|stop|enable|disable))",
    re.IGNORECASE,
)

# 只读 ssh 白名单（不拦）
SSH_READONLY_PATTERN = re.compile(
    rf"\bssh\b.*({ECS_DOMAIN_PATTERN}|{IP_PATTERN}).*"
    r"(git\s+(log|status|diff|ls-remote|show)|"
    r"systemctl\s+status|"
    r"journalctl|"
    r"\bls\b|\bcat\b|\bhead\b|\btail\b|\bgrep\b|\bwc\b|\bfind\b|"
    r"curl\s+.*(/health|/truth|/drift)|"
    r"python3?\s+.*(--help|qoder-bridge))",
    re.IGNORECASE,
)

# 提取 apply-<gate_id>*.py 的 gate_id
# 例：apply-b-layer-20260727.py → b-layer
#     apply-c-layer-drift-check-20260727.py → c-layer-drift-check
#     apply-meta-review-gate-20260725.py → meta-review-gate
# 规则：apply- 后到 -(YYYYMMDD|fix-YYYYMMDD|roundN-YYYYMMDD).py 前
GATE_ID_PATTERN = re.compile(
    r"\bapply-([a-z0-9-]+?)-(?:\d{8}|fix-\d{8}|round\d+-\d{8})\.py\b"
)


def get_override():
    """读 override 状态（30 分钟窗口）"""
    try:
        with open(OVERRIDE_FILE, "r") as f:
            d = json.load(f)
        if time.time() < d.get("until", 0):
            return d
    except Exception:
        pass
    return None


def extract_patch_filename(command):
    """从命令文本提取 apply-*.py 的完整文件名（精确）

    返回文件名（如 'apply-b-layer-20260727.py'）或 None。
    hook 用文件名查闸门表的 files 字段（精确等值），不再提取 gate_id 猜命名。
    """
    m = re.search(r"\b(apply-[a-z0-9-]+\.py)\b", command, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def load_gate_log():
    """YAML 解析（优先 pyyaml，降级手写）"""
    if not os.path.exists(GATE_LOG):
        return None, f"闸门日志表不存在: {GATE_LOG}"
    try:
        with open(GATE_LOG, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None, f"读闸门日志表失败: {e}"

    try:
        import yaml
        data = yaml.safe_load(content)
        if isinstance(data, list):
            return data, "ok"
    except ImportError:
        pass
    except Exception as e:
        return None, f"YAML 解析失败: {e}"

    # 降级手写解析（仅提 gate_id + verdict + files）
    entries = []
    current = {}
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("- "):
            if current:
                entries.append(current)
            current = {}
            s = s[2:].strip()
            if ":" in s:
                k, _, v = s.partition(":")
                k = k.strip()
                if k in ("gate_id", "verdict"):
                    current[k] = v.strip()
                elif k == "files":
                    current[k] = parse_yaml_list(v)
        elif s.startswith("- ") is False and ":" in line and current is not None and line.startswith("  "):
            k, _, v = line.strip().partition(":")
            k = k.strip()
            if k in ("gate_id", "verdict"):
                current[k] = v.strip()
            elif k == "files":
                current[k] = parse_yaml_list(v)
    if current:
        entries.append(current)
    return entries, "ok (fallback parser)"


def parse_yaml_list(v):
    """解析 YAML inline list [a, b] 或 [a]"""
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1]
        return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
    return [v] if v else []


def check_gate_by_filename(filename):
    """
    查 patch 文件名是否在闸门表某条目的 files 字段精确匹配，且 verdict=PASS。

    返回: (found_pass: bool, status: str, detail: str, open_gate_ids: list)
    """
    entries, err = load_gate_log()
    if entries is None:
        return False, "LOG_ERROR", err, []

    open_ids = []
    matches = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        eid = e.get("gate_id", "?")
        everdict = str(e.get("verdict", "")).strip()
        efiles = e.get("files", []) or []
        if not isinstance(efiles, list):
            efiles = [efiles]

        if everdict.upper() != "PASS":
            open_ids.append(f"{eid}({everdict})")

        # 文件名精确等值匹配（消灭子串推断）
        if filename in efiles:
            matches.append((eid, everdict))

    if not matches:
        return False, "NO_ENTRY", f"文件 '{filename}' 在闸门表 files 字段无精确匹配", open_ids

    latest = matches[-1]
    if latest[1].upper() == "PASS":
        return True, "PASS", f"文件 '{filename}' 匹配 gate_id='{latest[0]}' verdict=PASS", open_ids
    else:
        return False, latest[1], f"文件 '{filename}' 匹配 gate_id='{latest[0]}' verdict={latest[1]}（非 PASS）", open_ids


def infer_target_hint(command):
    """ssh 写路径但无 apply-*.py：从路径/服务名提取提示给用户（仅用于 deny 消息）"""
    m = re.search(r"/opt/pi-orchestrator/(?:extensions/)?([a-z0-9_-]+)\.?\w*", command)
    if m:
        return m.group(1)
    m = re.search(r"systemctl\s+\w+\s+pi-([a-z0-9-]+)", command)
    if m:
        return m.group(1)
    return None


def build_deny_reason(command, filename, target_hint, status, detail, open_ids):
    """构造 deny 提示"""
    open_list = "\n".join(f"  - {g}" for g in open_ids[:10]) if open_ids else "  (无 open 条目)"
    target_line = f"**提取的 patch 文件**: `{filename or '(无)'}`" if filename else f"**推断的目标**: `{target_hint or '(未识别)'}`（ssh 直接改 ECS，无 patch 文件名）"
    return (
        f"⚠️ **Pre-commit 评审闸门阻断**（governance-review-process.md §四.步骤0）\n\n"
        f"检测到 ECS 部署操作命中强制触发清单，但未找到 PASS 评审条目。\n\n"
        f"**命令**: `{command[:120]}{'...' if len(command) > 120 else ''}`\n"
        f"{target_line}\n"
        f"**状态**: {status}\n"
        f"**详情**: {detail}\n\n"
        f"**当前闸门表 open 条目**（核对 gate_id 拼写）:\n{open_list}\n\n"
        f"**解锁步骤**:\n"
        f"  1. 确认 patch 脚本命名（apply-<对象>-YYYYMMDD.py），闸门表对应条目的 files 字段含此文件名\n"
        f"  2. 新建 `archive/governance-review-<对象>-<date>/` 走三方评审\n"
        f"  3. PASS 后在 `pre-commit-review-gate-log.yaml` 追加条目（verdict: PASS, files: [文件名]）\n"
        f"  4. 重试本命令\n\n"
        f"**紧急 hotfix override**（不推荐，会留痕）:\n"
        f"  写 `{OVERRIDE_FILE}` 内容 `{{\"until\": <unix_ts_30min后>, \"reason\": \"<必填>\"}}`\n"
        f"  override 使用必须在闸门表追加 verdict=override 条目 + override_reason"
    )


def log_override_use(override_data):
    """override 被使用时，在闸门表追加留痕行（B-Q5）。

    注意：hook 只读不写 repo 文件（避免 hook 改 repo 造成副作用）。
    此函数仅打印提示，实际留痕靠 ZCode 自觉（spec 约束）。
    """
    # 仅 stdout 提示（hook stdout 在 deny 时显示给用户，在 pass 时不显示）
    # 这里靠 deny_reason 里的提示已经够了，不再额外动作
    pass


def main():
    try:
        raw = sys.stdin.buffer.read()
        hook_input = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return  # 解析失败不阻断（fail-open，避免 hook bug 卡死所有 Bash）

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Bash":
        return  # 只拦 Bash

    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        return

    # 检查 override（用于 deny 消息提示，但仍记录使用）
    override_data = get_override()
    if override_data:
        # override 生效 → 放行（但提示需留痕）
        # 注：override 放行时不阻断，提示靠下次 ZCode 自觉补表
        return

    # 判定是否命中强制触发
    is_transfer_apply = bool(TRANSFER_APPLY_PATTERN.search(command))
    is_ssh_write = bool(SSH_WRITE_PATTERN.search(command))

    # 只读 ssh 白名单优先放行
    if not is_transfer_apply and SSH_READONLY_PATTERN.search(command):
        return

    if not (is_transfer_apply or is_ssh_write):
        return  # 非强制触发，放行

    # 提取 patch 文件名（精确，消灭子串推断）
    filename = extract_patch_filename(command)
    target_hint = None
    if filename is None and is_ssh_write:
        # ssh 直接改 ECS 文件无 patch 文件名，给用户提示目标
        target_hint = infer_target_hint(command)

    # 查闸门表（文件名精确匹配 files 字段）
    if filename:
        found_pass, status, detail, open_ids = check_gate_by_filename(filename)
    else:
        # ssh 直接改 ECS：gate_id 推断无法精确，强制 deny 提示用户走 patch 脚本流程
        found_pass = False
        status = "NO_PATCH_FILE"
        detail = f"ssh 直接改 ECS 无 patch 文件名，无法精确匹配闸门表。目标提示: {target_hint}"
        # 仍读表拿 open_ids 展示
        entries, _ = load_gate_log()
        open_ids = []
        if entries:
            for e in entries:
                if isinstance(e, dict):
                    eid = e.get("gate_id", "?")
                    ev = str(e.get("verdict", "")).strip()
                    if ev.upper() != "PASS":
                        open_ids.append(f"{eid}({ev})")

    if found_pass:
        return  # 放行

    # deny
    reason = build_deny_reason(command, filename, target_hint, status, detail, open_ids)
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    sys.exit(2)


if __name__ == "__main__":
    main()
