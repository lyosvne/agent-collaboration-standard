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
# SO-8: override 补录强制校验。override 触发时写 pending log（本地状态，不进 repo），
# 下次 hook 触发时校验闸门表是否有 verdict=override 条目，无则 deny（防"事后补退化为事后忘"）。
OVERRIDE_PENDING_FILE = os.path.join(SCRIPT_DIR, ".review-gate-override-pending.json")

# repo root 推断：hook 位于 <repo>/.zcode/hooks/，向上两级是 repo root
# 环境变量优先（测试用），否则用脚本位置推断（团队 clone 零配置）
# B-config round3：变量未定义且脚本路径推断失败时，下游 fail-closed（check_gate 返回 None）
_DEFAULT_REPO = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REPO_ROOT = os.environ.get("AGENT_COLLABORATION_REPO") or _DEFAULT_REPO
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


# ===== SO-8: override 补录强制校验（round2: override_id 精确匹配）=====

def _atomic_write_json(path, data):
    """原子写 JSON（A round2 建议：tmp + rename，避免断电损坏）。

    失败不抛异常（紧急 hotfix 不能因日志写失败卡死），返回 bool。
    """
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Unix 下设 0600（B round2 建议）；Windows 下 chmod 可能无效但不报错
        try:
            os.chmod(tmp, 0o600)
        except Exception:
            pass
        os.replace(tmp, path)  # 原子 rename
        return True
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False


def _gen_override_id():
    """生成 override 唯一 id（round2 精确匹配用）。

    格式：时间戳后10位 + 进程pid 后4位，保证单机内唯一性（pre-commit 串行）。
    """
    return f"{int(time.time())}-{os.getpid() & 0xFFFF}"


def append_override_pending(reason, filename, command):
    """override 触发时追加 pending 记录（本地状态，不进 repo）。

    每条记录含唯一 override_id，闸门表补录时必须回填相同 override_id 才能清理。
    """
    pending = []
    try:
        with open(OVERRIDE_PENDING_FILE, "r", encoding="utf-8") as f:
            pending = json.load(f)
        if not isinstance(pending, list):
            pending = []
    except Exception:
        pass

    now_ts = time.time()
    entry = {
        "override_id": _gen_override_id(),
        "used_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now_ts)),
        "used_at_ts": now_ts,
        "reason": reason or "(无 reason)",
        "filename": filename or "(未识别)",
        "command_head": (command or "")[:120],
    }
    pending.append(entry)
    _atomic_write_json(OVERRIDE_PENDING_FILE, pending)


def check_override_pending_backfilled():
    """校验 pending log 里的 override 是否已在闸门表补录（round2: 逐条 override_id 精确匹配）。

    返回: (all_backfilled: bool, unmatched_count: int, detail: str)
    """
    if not os.path.exists(OVERRIDE_PENDING_FILE):
        return True, 0, "无 pending 记录"

    pending = []
    try:
        with open(OVERRIDE_PENDING_FILE, "r", encoding="utf-8") as f:
            pending = json.load(f)
        if not isinstance(pending, list):
            pending = []
    except Exception as e:
        # 解析失败 fail-closed（A/B 共识）
        return False, -1, f"pending log 损坏: {e}（建议 rm {OVERRIDE_PENDING_FILE}）"

    if not pending:
        return True, 0, "pending 为空"

    # 读闸门表，收集所有已补录的 override_id（verdict=override + override_reason.strip() 非空 + override_id 非空）
    entries, err = load_gate_log()
    if entries is None:
        return False, len(pending), f"闸门表不可读无法校验 override 补录: {err}"

    backfilled_ids = set()
    for e in entries:
        if not isinstance(e, dict):
            continue
        if str(e.get("verdict", "")).strip().lower() == "override":
            reason = str(e.get("override_reason", "")).strip()  # round2: .strip() 归一化
            oid = str(e.get("override_id", "")).strip()
            if reason and oid:  # 必须有 override_id 且 reason 非空才算补录
                backfilled_ids.add(oid)

    # 逐条匹配
    unmatched = [p for p in pending if p.get("override_id") not in backfilled_ids]
    if not unmatched:
        return True, 0, "全部 pending 已补录"
    else:
        sample = unmatched[-1]
        ids_list = [p.get("override_id", "?") for p in unmatched]
        return False, len(unmatched), (
            f"检测到 {len(unmatched)} 条未补录 override（共 {len(pending)} 条 pending，"
            f"已补 {len(pending) - len(unmatched)} 条）。未补录 override_id: {ids_list[:5]}"
        )


def clear_matched_override_pending():
    """清理已被闸门表补录的 pending 记录（round2: 逐条按 override_id 清理，未匹配的保留）。"""
    if not os.path.exists(OVERRIDE_PENDING_FILE):
        return

    try:
        with open(OVERRIDE_PENDING_FILE, "r", encoding="utf-8") as f:
            pending = json.load(f)
        if not isinstance(pending, list):
            return
    except Exception:
        return  # 损坏时不清理（让 check 路径处理）

    entries, _ = load_gate_log()
    if entries is None:
        return

    backfilled_ids = set()
    for e in entries:
        if isinstance(e, dict) and str(e.get("verdict", "")).strip().lower() == "override":
            reason = str(e.get("override_reason", "")).strip()
            oid = str(e.get("override_id", "")).strip()
            if reason and oid:
                backfilled_ids.add(oid)

    remaining = [p for p in pending if p.get("override_id") not in backfilled_ids]

    if len(remaining) == len(pending):
        return  # 无变化，不写

    if not remaining:
        # 全清理：直接删文件
        try:
            os.remove(OVERRIDE_PENDING_FILE)
        except Exception:
            pass
    else:
        _atomic_write_json(OVERRIDE_PENDING_FILE, remaining)





def extract_patch_filename(command):
    """从命令文本提取 apply-*.py 的完整文件名（精确）

    返回文件名（如 'apply-b-layer-20260727.py'）或 None。
    hook 用文件名查闸门表的 files 字段（精确等值），不再提取 gate_id 猜命名。
    B-Q3 round3：强制小写归一化（Windows 大小写不敏感场景兼容）。
    """
    m = re.search(r"\b(apply-[a-z0-9-]+\.py)\b", command, re.IGNORECASE)
    if m:
        return m.group(1).lower()
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
    # B-Q3 round3：files 字段统一小写归一化（与 extract_patch_filename 对齐）
    target = (filename or "").lower()
    for e in entries:
        if not isinstance(e, dict):
            continue
        eid = e.get("gate_id", "?")
        everdict = str(e.get("verdict", "")).strip()
        efiles = e.get("files", []) or []
        if not isinstance(efiles, list):
            efiles = [efiles]
        # 归一化为小写字符串列表
        efiles_norm = [str(f).strip().lower() for f in efiles if str(f).strip()]

        if everdict.upper() != "PASS":
            open_ids.append(f"{eid}({everdict})")

        # 文件名精确等值匹配（消灭子串推断），归一化小写比较（B-Q3 round3）
        if target and target in efiles_norm:
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
        f"  **SO-8 强制校验**: override 使用会在 pending log 记录，下次部署前若闸门表无 verdict=override 条目会被拦"
    )


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

    # 检查 override（SO-8: 放行前追加 pending log，留下次校验）
    override_data = get_override()
    if override_data:
        # override 生效 → 放行，但记 pending（下次非 override 触发会校验是否已补闸门表）
        filename_hint = extract_patch_filename(command)
        append_override_pending(
            override_data.get("reason", "(无 reason)"),
            filename_hint,
            command,
        )
        return

    # 判定是否命中强制触发
    is_transfer_apply = bool(TRANSFER_APPLY_PATTERN.search(command))
    is_ssh_write = bool(SSH_WRITE_PATTERN.search(command))

    # 只读 ssh 白名单优先放行
    if not is_transfer_apply and SSH_READONLY_PATTERN.search(command):
        return

    if not (is_transfer_apply or is_ssh_write):
        return  # 非强制触发，放行

    # SO-8: 命中强制触发后，先校验是否有未补录的 override（B-Q5 真阻断）
    backfilled, unmatched_count, pending_detail = check_override_pending_backfilled()

    # 无论是否全部补录，都先清理已匹配的 pending（round2 T3: 部分补录场景下清已补的）
    clear_matched_override_pending()

    if not backfilled:
        reason = (
            f"⚠️ **Pre-commit 评审闸门阻断（override 未补录）**\n\n"
            f"检测到 {unmatched_count} 条 override 使用未在闸门表补录条目。\n\n"
            f"**详情**: {pending_detail}\n\n"
            f"**为何阻断**: override 紧急放行后必须在闸门表补 verdict=override 条目（含相同 override_id），"
            f"否则审计链断（B-Q5: '事后补退化为事后忘'；round2: 精确匹配防首次成功后永久失效）。\n\n"
            f"**解锁步骤**:\n"
            f"  1. 在 `governance/specs/pre-commit-review-gate-log.yaml` 追加条目，**override_id 必须与 pending 一致**:\n"
            f"     ```yaml\n"
            f"     - gate_id: <对象>\n"
            f"       files: [<patch 文件名>]\n"
            f"       verdict: override\n"
            f"       override_id: <上面列出的 override_id>\n"
            f"       override_reason: \"<紧急 hotfix 原因>\"\n"
            f"       override_date: <YYYY-MM-DD>\n"
            f"       trigger_class: [...]\n"
            f"       commit_sha: <sha>\n"
            f"     ```\n"
            f"  2. 重试本命令（hook 按 override_id 逐条匹配，已补的清理，未补的仍 deny）\n\n"
            f"  **注**: override 条目仅完成审计补录，本次部署仍需 PASS 条目才能放行（verdict=override ≠ verdict=PASS）。\n\n"
            f"**或手动清理 pending**（如 override 是误触发）:\n"
            f"  `rm {OVERRIDE_PENDING_FILE}`"
        )
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        sys.exit(2)

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
