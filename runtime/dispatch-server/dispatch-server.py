#!/usr/bin/env python3
"""
调度上下文 HTTP 端点（dispatch-server.py）

功能：暴露 ECS 上的调度上下文给所有智能体读取。
- Qoder Cloud Agent 通过 WebFetch 读
- ZCode 通过 curl 读
- 任何调度者都能看到最新进展

监听 127.0.0.1:8765，由 Caddy 反代 /dispatch/* 对外暴露。

端点：
  GET  /dispatch/all              聚合全部上下文（一次 WebFetch 拿全）
  GET  /dispatch/context          项目知识（CONTEXT.md）
  GET  /dispatch/fleet            编队状态（fleet-status.json）
  GET  /dispatch/history/<agent>  某个 agent 的调度历史
  GET  /dispatch/models           三档当前 model id + 最新可用模型对比
  POST /dispatch/history/<agent>  追加调度记录（需 key 认证）
  GET  /dispatch/health           健康检查
"""
import os
import subprocess
import hashlib
import hmac
import json
import math
import re
import time
import urllib.request
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ─── 配置 ──────────────────────────────────────────────


def positive_int_env(name, default):
    value = int(os.environ.get(name, default))
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def positive_float_env(name, default):
    value = float(os.environ.get(name, default))
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return value


DISPATCH_DIR = os.environ.get("DISPATCH_DIR", "/opt/pi/dispatch")
PORT = int(os.environ.get("DISPATCH_PORT", "8765"))
AUTH_KEY = os.environ.get("DISPATCH_KEY", "")
MODEL_CACHE_TTL_SECONDS = int(os.environ.get("MODEL_CACHE_TTL_SECONDS", "300"))
MAX_HISTORY_BODY_BYTES = positive_int_env("MAX_HISTORY_BODY_BYTES", "65536")
HISTORY_BODY_READ_TIMEOUT_SECONDS = positive_float_env(
    "HISTORY_BODY_READ_TIMEOUT_SECONDS", "5"
)
_MODEL_CACHE = {"expires_at": 0.0, "value": None}

# 治理文档源（双源 fallback: governance-mirror 优先, GitHub raw 兜底）
# 注意: ECS 上治理文档在 governance-mirror/repo/governance/（不是 repo/standards/）
# START_HERE.md 在仓库根 governance-mirror/repo/START_HERE.md
GOVERNANCE_DIR = os.environ.get("GOVERNANCE_DIR", "/opt/pi/governance-mirror/repo/governance")
GOVERNANCE_ROOT = os.environ.get("GOVERNANCE_ROOT", "/opt/pi/governance-mirror/repo")  # 仓库根, 读 START_HERE
GITHUB_RAW_BASE = os.environ.get(
    "GITHUB_RAW_BASE",
    "https://raw.githubusercontent.com/lyosvne/agent-collaboration-standard/master"
)

# drift 治理（drift-cron.sh 每 30min 写入）
DRIFT_LATEST = os.environ.get("DRIFT_LATEST", "/opt/pi-orchestrator/logs/drift-latest.json")
# PATCH-B-LAYER-FIX-20260727-APPLIED
# PATCH-B-LAYER-AUTH-20260727-APPLIED

# 治理文档文件名映射（端点名 → 文件相对路径）
# north-star/architecture/fleet-division/roadmap 在 governance/; start-here 在仓库根
GOVERNANCE_FILES = {
    "north-star": "north-star-v1.2.md",
    "architecture": "agent-matrix-architecture-v1.0.md",
    "fleet-division": "fleet-division-v1.1.md",
    "roadmap": "global-roadmap-v1.1.md",
    "start-here": "START_HERE.md",  # 在仓库根, 不在 governance/
}

GOVERNANCE_MANIFEST_KEYS = {
    "north-star": "northStar",
    "architecture": "architecture",
    "fleet-division": "fleetDivision",
    "roadmap": "roadmap",
}

# 三档 agent 配置（和 qoder-bridge.py 保持一致）
TIERS = {
    "general": {
        "agent_id": "agent_00k8fo5p79rsw03oyb18",
        "model_id": "qmodel_preview",
        "model_name": "Qwen3.8-Max-Preview"
    },
    "frontend": {
        "agent_id": "agent_00k8fo69ixeyo6z3txle",
        "model_id": "kmodel_latest",
        "model_name": "Kimi-K3"
    },
    "cantus": {
        "agent_id": "agent_00k8fo6sj5s008avf3bl",
        "model_id": "cmodel",
        "model_name": "Cantus"
    },
}

VALID_AGENTS = list(TIERS.keys()) + ["kimi", "zcode", "trae", "mira", "pi"]


def log(msg):
    line = f"[{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}] {msg}"
    print(line, flush=True)


def read_file(path, default="（文件不存在）"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return default
    except Exception:
        return "（读取失败）"


def sanitize_history_field(value, limit):
    """Normalize untrusted history fields to a bounded single Markdown line."""
    text = str(value).replace("`", "'")
    text = "".join(
        character if character >= " " and character != "\x7f" else " "
        for character in text
    )
    return " ".join(text.split())[:limit]


def read_governance_github_file(filename):
    """Read a governance document from the public GitHub raw fallback."""
    try:
        if filename == "START_HERE.md":
            url = f"{GITHUB_RAW_BASE}/{filename}"
        else:
            url = f"{GITHUB_RAW_BASE}/governance/{filename}"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "dispatch-server")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8"), "github"
    except Exception:
        return f"（治理文档 {filename} 不可达: mirror 和 github 都失败）", "missing"


def read_governance_file(filename):
    """读治理文档: 优先 governance-mirror, fallback GitHub raw。

    返回 (content, source)。source = 'mirror' / 'github' / 'missing'。

    双源策略（解决传播缺失诊断 §三 的根因 1+3）:
      - mirror: ECS 本地 /opt/pi/governance-mirror/repo/（Pi cron 从 git pull, 与 git 真值同步）
      - github: GitHub raw 兜底（mirror 不可达时, 保证治理文档仍可读）
    """
    # 1. 尝试 governance-mirror 本地（START_HERE 在仓库根, 其他在 governance/）
    if filename == "START_HERE.md":
        mirror_path = f"{GOVERNANCE_ROOT}/{filename}"
    else:
        mirror_path = f"{GOVERNANCE_DIR}/{filename}"
    content = read_file(mirror_path, None)
    if content and content != "（文件不存在）" and "（读取失败" not in content:
        return content, "mirror"
    # 2. fallback GitHub raw（START_HERE 在仓库根, 其他在 governance/）
    return read_governance_github_file(filename)


def governance_git_command(*args):
    """Build a fixed Git command for the root-owned governance mirror."""
    return [
        "git",
        "-c",
        f"safe.directory={GOVERNANCE_ROOT}",
        "-C",
        GOVERNANCE_ROOT,
        *args,
    ]


def get_mirror_head():
    """Return the governance mirror HEAD without exposing repository paths."""
    try:
        result = subprocess.run(
            governance_git_command("rev-parse", "HEAD"),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def read_snapshot_file(commit_sha, relative_path):
    """Read one file as bytes from an exact governance Git commit."""
    if not commit_sha:
        return None, "commit-missing"
    try:
        result = subprocess.run(
            governance_git_command("show", f"{commit_sha}:{relative_path}"),
            capture_output=True,
            timeout=5,
        )
    except Exception:
        return None, "unavailable"
    if result.returncode != 0:
        return None, "missing"
    return result.stdout, "ok"


def snapshot_file_commit_time(commit_sha, relative_path):
    """Return the last commit time for a file within the captured snapshot."""
    if not commit_sha:
        return None
    try:
        result = subprocess.run(
            governance_git_command(
                "log",
                "-1",
                "--format=%cI",
                commit_sha,
                "--",
                relative_path,
            ),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_version_manifest(commit_sha):
    """Read the canonical version manifest from the exact mirror HEAD."""
    raw, status = read_snapshot_file(
        commit_sha, "governance/version-manifest.json"
    )
    if status != "ok":
        return None, status
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "malformed"
    if (
        not isinstance(manifest, dict)
        or manifest.get("schemaVersion") != 1
        or not isinstance(manifest.get("canonicalDocuments"), dict)
    ):
        return None, "invalid"
    return manifest, "ok"


def get_available_models():
    """从 Qoder API 拉最新可用模型列表"""
    pat = os.environ.get("QODER_PAT", "")
    if not pat:
        return {"error": "QODER_PAT 未设置"}
    try:
        req = urllib.request.Request("https://api.qoder.com/api/v1/cloud/models")
        req.add_header("Authorization", f"Bearer {pat}")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        log(f"Qoder models upstream unavailable: {type(exc).__name__}")
        return {"error": "upstream unavailable"}


class DispatchHandler(BaseHTTPRequestHandler):
    def _send_text(self, text, status=200, content_type="text/plain; charset=utf-8"):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data, status=200):
        self._send_text(json.dumps(data, ensure_ascii=False, indent=2), status,
                        "application/json; charset=utf-8")

    def _send_governance(self, content, source, title):
        """发送治理文档, 顶部标注来源（方便诊断传播缺失）。"""
        header = f"> {title} | 来源: {source}\n\n"
        self._send_text(header + content)

    def _require_auth(self):
        """Protect runtime and write endpoints with header-only fail-closed auth."""
        if not AUTH_KEY:
            self._send_json({"error": "dispatch authentication is not configured"}, 503)
            return False
        provided = self.headers.get("X-Dispatch-Key", "")
        authorization = self.headers.get("Authorization", "")
        if not provided and authorization.startswith("Bearer "):
            provided = authorization[7:]
        if not provided or not hmac.compare_digest(provided, AUTH_KEY):
            self._send_text("认证失败", 403)
            return False
        return True

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        parts = [p for p in path.split("/") if p]
        if "key" in parse_qs(parsed.query, keep_blank_values=True):
            return self._send_text("query string credentials are not accepted", 400)

        protected = (
            parts in (
                ["dispatch", "all"],
                ["dispatch", "context"],
                ["dispatch", "fleet"],
                ["dispatch", "survey"],
                ["dispatch", "models"],
                ["dispatch", "health"],
                ["dispatch", "drift"],
            )
            or (len(parts) == 3 and parts[:2] == ["dispatch", "history"])
        )
        if protected and not self._require_auth():
            return

        # /dispatch/all
        if parts == ["dispatch", "all"]:
            return self._handle_all()

        # /dispatch/context
        if parts == ["dispatch", "context"]:
            return self._send_text(read_file(f"{DISPATCH_DIR}/CONTEXT.md"))

        # /dispatch/fleet
        if parts == ["dispatch", "fleet"]:
            return self._send_text(read_file(f"{DISPATCH_DIR}/fleet-status.json"))

        # /dispatch/roadmap
        if parts == ["dispatch", "roadmap"]:
            return self._send_text(read_file(f"{DISPATCH_DIR}/global-roadmap-v1.1.md"))

        # /dispatch/survey
        if parts == ["dispatch", "survey"]:
            return self._send_text(read_file(f"{DISPATCH_DIR}/survey-zcode.md"))

        # /dispatch/north-star（北极星 v1.2）
        if parts == ["dispatch", "north-star"]:
            content, source = read_governance_file(GOVERNANCE_FILES["north-star"])
            return self._send_governance(content, source, "北极星 v1.2")

        # /dispatch/architecture（协作矩阵 / 架构真值 v1.0）
        if parts == ["dispatch", "architecture"]:
            content, source = read_governance_file(GOVERNANCE_FILES["architecture"])
            return self._send_governance(content, source, "协作矩阵 / 架构真值 v1.0")

        # /dispatch/fleet-division（编队分工 v1.1）
        if parts == ["dispatch", "fleet-division"]:
            content, source = read_governance_file(GOVERNANCE_FILES["fleet-division"])
            return self._send_governance(content, source, "编队分工 v1.1")

        # /dispatch/start-here（全局启动入口）
        if parts == ["dispatch", "start-here"]:
            content, source = read_governance_file(GOVERNANCE_FILES["start-here"])
            return self._send_governance(content, source, "全局启动入口 START_HERE.md")

        # /dispatch/history/<agent>
        if len(parts) == 3 and parts[0] == "dispatch" and parts[1] == "history":
            agent = parts[2]
            if agent not in VALID_AGENTS:
                return self._send_text("未知 agent", 404)
            return self._send_text(read_file(f"{DISPATCH_DIR}/{agent}/history.md"))

        # /dispatch/models
        if parts == ["dispatch", "models"]:
            return self._handle_models()

        # /dispatch/health
        if parts == ["dispatch", "health"]:
            return self._handle_health()

        # /dispatch/truth/versions（治理文档版本清单, 时序版本自动化）
        if parts == ["dispatch", "truth", "versions"]:
            return self._handle_truth_versions()

        # /dispatch/drift（漂移体检最新报告）
        if parts == ["dispatch", "drift"]:
            return self._handle_drift()

        self._send_text(f"未知端点: {path}\n可用: /dispatch/all, /dispatch/context, "
                        f"/dispatch/north-star, /dispatch/architecture, /dispatch/fleet-division, "
                        f"/dispatch/start-here, /dispatch/roadmap, /dispatch/fleet, "
                        f"/dispatch/history/<agent>, /dispatch/models, /dispatch/health,\n                        /dispatch/truth/versions, /dispatch/drift", 404)

    def _handle_all(self):
        """聚合全部上下文，一次返回"""
        sections = []

        sections.append("# 编队调度上下文（聚合）")
        sections.append(f"\n> 更新时间: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")

        sections.append("\n---\n## 项目知识\n")
        sections.append(read_file(f"{DISPATCH_DIR}/CONTEXT.md"))

        sections.append("\n---\n## 编队状态\n")
        fleet_raw = read_file(f"{DISPATCH_DIR}/fleet-status.json")
        try:
            fleet = json.loads(fleet_raw)
            sections.append(json.dumps(fleet, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            sections.append(fleet_raw)

        # 治理文档（从 governance-mirror 或 GitHub raw, 解决传播缺失）
        # 顺序: 北极星 → 架构 → 分工 → 路线图 → 启动入口
        gov_titles = {
            "north-star": "北极星（方向）",
            "architecture": "协作矩阵 / 架构真值",
            "fleet-division": "编队分工（G/M 双环）",
            "roadmap": "全局路线图",
            "start-here": "全局启动入口",
        }
        for key, title in gov_titles.items():
            content, source = read_governance_file(GOVERNANCE_FILES[key])
            if source != "missing":
                sections.append(f"\n---\n## {title}（来源: {source}）\n")
                sections.append(content)
            else:
                sections.append(f"\n---\n## {title}\n> ⚠️ {content}\n")

        sections.append("\n---\n## 各档位调度历史\n")
        for tier in TIERS:
            hist = read_file(f"{DISPATCH_DIR}/{tier}/history.md")
            # 只取最后 20 行避免太长
            lines = hist.strip().split("\n")
            if len(lines) > 25:
                hist = "\n".join(lines[:5] + ["...（省略中间部分）..."] + lines[-20:])
            sections.append(f"### {tier}\n```\n{hist}\n```\n")

        self._send_text("\n".join(sections))

    def _handle_health(self):
        """健康检查 + governance 文档状态报告（诊断传播缺失）。"""
        governance_status = {}
        for key, filename in GOVERNANCE_FILES.items():
            _, source = read_governance_file(filename)
            governance_status[key] = source
        self._send_json({
            "status": "ok",
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "github_raw_base": GITHUB_RAW_BASE,
            "tiers": list(TIERS.keys()),
            "governance_files": governance_status
        })

    def _handle_truth_versions(self):
        """治理文档版本清单（时序版本自动化, 各域自校验对齐）。

        消费者契约（2026-07-27 评审修复后）:
        - version: 文件名 -vX.Y[.Z] 解析, 用 split+int 比较（非字符串比较）
        - versioned: False 表示非时序版本文件（如 START_HERE.md）, 跳过版本校验
        - commit_sha: governance-mirror HEAD（全局, 所有文档同源）, mirror 落后 github 时消费者可能误判, 需结合 mtime 判断新鲜度
        - content_sha12: 文件内容 sha256 前 12 位, 同版本号下内容变化可检测
        - mtime: 捕获 HEAD 中该文件最后一次 Git 提交时间
        - source: mirror/github/missing, mirror=本地快照, github=raw 兜底, missing=双源失败
        - logical_version: 同一 HEAD 的 version-manifest 逻辑版本
        - degraded: manifest、快照或 fallback 不一致时显式告警

        对应 archive/governance-review-node1 §5.3 设计（version/updated/commit-hash）。
        """
        # Capture mirror HEAD once; all healthy metadata is read from this object.
        commit_sha = get_mirror_head()

        manifest, manifest_status = read_version_manifest(commit_sha)
        manifest_documents = (
            manifest["canonicalDocuments"] if manifest_status == "ok" else {}
        )
        versions = {}
        for key, filename in GOVERNANCE_FILES.items():
            # 正则放宽: 支持 1-3 段 semver（v1.2 / v1.2.3）
            m = re.search(r"-v(\d+(?:\.\d+){0,2})\.md$", filename)
            version = m.group(1) if m else None
            versioned = m is not None
            logical_version = None
            degraded_reasons = []
            relative_path = (
                filename
                if filename == "START_HERE.md"
                else f"governance/{filename}"
            )
            raw, snapshot_status = read_snapshot_file(commit_sha, relative_path)
            if snapshot_status == "ok":
                source = "mirror"
                content_sha12 = hashlib.sha256(raw).hexdigest()[:12]
                mtime = snapshot_file_commit_time(commit_sha, relative_path)
                if mtime is None:
                    degraded_reasons.append("document-time-unavailable")
            else:
                fallback_content, source = read_governance_github_file(filename)
                content_sha12 = (
                    hashlib.sha256(fallback_content.encode("utf-8")).hexdigest()[:12]
                    if source == "github"
                    else None
                )
                mtime = None
                degraded_reasons.append(f"snapshot-{snapshot_status}")

            manifest_key = GOVERNANCE_MANIFEST_KEYS.get(key)
            if versioned:
                if manifest_status != "ok":
                    degraded_reasons.append(f"manifest-{manifest_status}")
                else:
                    entry = manifest_documents.get(manifest_key)
                    expected_path = f"governance/{filename}"
                    if not isinstance(entry, dict):
                        degraded_reasons.append("manifest-entry-missing")
                    elif entry.get("status") != "active":
                        degraded_reasons.append("manifest-entry-inactive")
                    elif entry.get("path") != expected_path:
                        degraded_reasons.append("manifest-path-mismatch")
                    else:
                        manifest_version = entry.get("version")
                        if (
                            isinstance(manifest_version, str)
                            and re.fullmatch(
                                r"v?\d+(?:\.\d+){0,2}", manifest_version
                            )
                        ):
                            logical_version = manifest_version.removeprefix("v")
                        else:
                            degraded_reasons.append("manifest-version-invalid")
            if source != "mirror":
                degraded_reasons.append(f"document-source-{source}")

            versions[key] = {
                "filename": filename,
                "version": version,
                "versioned": versioned,
                "logical_version": logical_version,
                "filename_version": version,
                "version_source": (
                    "manifest"
                    if logical_version is not None
                    else "filename"
                    if versioned
                    else "unversioned"
                ),
                "degraded": bool(degraded_reasons),
                "degraded_reasons": degraded_reasons,
                "missing": source == "missing",
                "commit_sha": commit_sha,
                "content_sha12": content_sha12,
                "mtime": mtime,
                "source": source,
            }
        final_head = get_mirror_head()
        if commit_sha is not None and final_head != commit_sha:
            for document in versions.values():
                document["degraded"] = True
                document["degraded_reasons"].append("mirror-head-changed")
        self._send_json({
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "github_raw_base": GITHUB_RAW_BASE,
            "manifest_status": manifest_status,
            "degraded": any(document["degraded"] for document in versions.values()),
            "documents": versions,
        })

    def _handle_drift(self):
        """漂移体检最新报告（drift-cron.sh 每 30min 写入 drift-latest.json）。

        认证:
        - 使用 X-Dispatch-Key 或 Authorization: Bearer
        - query string key 被拒绝，避免 access-log 泄露
        - DISPATCH_KEY 缺失时 fail-closed 返回 503

        消费者契约（2026-07-27 评审修复后, fail-closed）:
        - HTTP 200 + 合法 JSON: drift 报告正常, 含 timestamp + branches 数组
        - HTTP 403 "认证失败": header key 缺失或不匹配
        - HTTP 503: DISPATCH_KEY 未配置
        - HTTP 502 + {"error": ...}: drift-latest.json 缺失 / 不可读 / JSON 损坏
          （消费者必须把 502 视为 drift 系统异常, 不是"无漂移"）
        - 正常的零漂移状态也会是 {"timestamp": "...", "branches": [...]}, 而非空 {}
          （空 {} 在修复前被当 200 返回是 fail-open, 已修）
        """
        raw = read_file(DRIFT_LATEST, None)
        if raw is None or raw == "（文件不存在）" or "（读取失败" in raw:
            self._send_json({
                "error": "drift report unavailable",
                "missing": True,
                "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, 502)
            return
        try:
            data = json.loads(raw)
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json({
                "error": "drift report malformed",
                "detail": type(e).__name__,
                "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, 502)
            return
        self._send_json(data)

    def _handle_models(self):
        """三档当前配置 + 最新可用模型对比"""
        now = time.time()
        if _MODEL_CACHE["value"] is None or now >= _MODEL_CACHE["expires_at"]:
            _MODEL_CACHE["value"] = get_available_models()
            _MODEL_CACHE["expires_at"] = now + MODEL_CACHE_TTL_SECONDS
        available = _MODEL_CACHE["value"]
        avail_ids = []
        if isinstance(available, dict) and "data" in available:
            avail_ids = [m.get("id", "") for m in available["data"]]

        result = {"tiers": {}, "model_available": {}}
        for tier, cfg in TIERS.items():
            mid = cfg["model_id"]
            result["tiers"][tier] = {
                "agent_id": cfg["agent_id"],
                "model_id": mid,
                "model_name": cfg["model_name"],
                "still_available": mid in avail_ids if avail_ids else "unknown"
            }
        result["model_available"]["all_ids"] = avail_ids
        result["model_available"]["count"] = len(avail_ids)
        self._send_json(result)

    def do_POST(self):
        parsed = urlparse(self.path)
        if "key" in parse_qs(parsed.query, keep_blank_values=True):
            return self._send_text("query string credentials are not accepted", 400)
        parts = [p for p in parsed.path.rstrip("/").split("/") if p]

        # POST /dispatch/history/<agent>
        if len(parts) == 3 and parts[0] == "dispatch" and parts[1] == "history":
            agent = parts[2]
            return self._handle_append_history(agent)

        self._send_text(f"未知 POST 端点: {parsed.path}", 404)

    def _handle_append_history(self, agent):
        """追加调度记录到 history.md"""
        if not self._require_auth():
            return
        if agent not in VALID_AGENTS:
            return self._send_text("未知 agent", 404)

        # 读 body。限制大小和读取时间，避免单线程服务被异常客户端阻塞。
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._send_text("Content-Length 无效", 400)
        if content_length < 0:
            return self._send_text("Content-Length 无效", 400)
        if content_length > MAX_HISTORY_BODY_BYTES:
            return self._send_text("请求体过大", 413)

        body_bytes = b""
        if content_length:
            previous_timeout = self.connection.gettimeout()
            deadline = time.monotonic() + HISTORY_BODY_READ_TIMEOUT_SECONDS
            read_error = None
            try:
                chunks = []
                remaining = content_length
                while remaining:
                    timeout = deadline - time.monotonic()
                    if timeout <= 0:
                        read_error = ("请求体读取超时", 408)
                        break
                    self.connection.settimeout(timeout)
                    chunk = self.rfile.read1(min(8192, remaining))
                    if not chunk:
                        read_error = ("请求体长度不完整", 400)
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                if read_error is None:
                    body_bytes = b"".join(chunks)
            except (TimeoutError, OSError):
                read_error = ("请求体读取超时", 408)
            finally:
                self.connection.settimeout(previous_timeout)
            if read_error is not None:
                message, status = read_error
                return self._send_text(message, status)

        try:
            body = body_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return self._send_text("请求体必须是 UTF-8", 400)
        if not body:
            return self._send_text("请求体为空", 400)

        # 解析记录（期望 JSON: {caller, task, result, status}）
        try:
            record = json.loads(body)
        except json.JSONDecodeError:
            return self._send_text("请求体不是合法 JSON", 400)
        if not isinstance(record, dict):
            return self._send_text("请求体必须是 JSON object", 400)
        for field in ("caller", "task", "status", "session_id", "result"):
            if field in record and not isinstance(record[field], str):
                return self._send_text(f"字段 {field} 必须是字符串", 400)
        if "duration" in record and not isinstance(record["duration"], (str, int, float)):
            return self._send_text("字段 duration 类型无效", 400)

        caller = sanitize_history_field(record.get("caller", "unknown"), 100)
        task = sanitize_history_field(record.get("task", ""), 200)
        status = sanitize_history_field(record.get("status", "unknown"), 50)
        session_id = sanitize_history_field(record.get("session_id", ""), 100)
        duration = sanitize_history_field(record.get("duration", ""), 50)
        result_text = sanitize_history_field(record.get("result", ""), 500)

        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        entry = f"\n### [{ts}] 调度者: {caller}\n"
        entry += f"- **任务**: {task}\n"
        entry += f"- **状态**: {status}\n"
        if record.get("session_id"):
            entry += f"- **会话**: {session_id}\n"
        if record.get("duration"):
            entry += f"- **耗时**: {duration}s\n"
        if result_text:
            entry += f"- **结果摘要**: {result_text}\n"

        hist_path = f"{DISPATCH_DIR}/{agent}/history.md"
        hist_dir = os.path.dirname(hist_path)
        os.makedirs(hist_dir, exist_ok=True)

        # 追加（不覆盖）
        existing = read_file(hist_path, "")
        with open(hist_path, "w", encoding="utf-8") as f:
            f.write(existing + entry)

        log(f"追加调度记录: agent={agent} caller={caller}")
        self._send_text(f"已追加记录到 {agent}/history.md")

    def log_message(self, format, *args):
        # 静默默认日志，用自定义 log
        pass


def main():
    log(f"启动 dispatch-server，监听 127.0.0.1:{PORT}")
    log(f"调度上下文目录: {DISPATCH_DIR}")
    tier_info = ", ".join(f"{t}={TIERS[t]['model_id']}" for t in TIERS)
    log(f"三档配置: {tier_info}")

    server = HTTPServer(("127.0.0.1", PORT), DispatchHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("收到中断，关闭")
        server.shutdown()


if __name__ == "__main__":
    main()
