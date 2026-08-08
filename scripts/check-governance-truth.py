#!/usr/bin/env python3

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "governance/version-manifest.json"


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"missing frontmatter: {path.relative_to(ROOT)}")
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            return result
        key, separator, value = line.partition(":")
        if separator:
            result[key.strip()] = value.strip().strip('"')
    raise ValueError(f"unterminated frontmatter: {path.relative_to(ROOT)}")


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    )
    return [ROOT / item for item in output.split("\0") if item]


def secret_patterns() -> list[re.Pattern[str]]:
    fine_prefix = "_".join(["github", "pat"]) + "_"
    github_prefixes = ["".join(["gh", suffix]) + "_" for suffix in "pousr"]
    begin_private = "-----" + "BEGIN " + "(?:RSA |EC |OPENSSH )?" + "PRIVATE KEY-----"
    aws_prefix = "".join(["AK", "IA"])
    slack_prefix = "".join(["xo", "x"])
    return [
        re.compile(re.escape(fine_prefix) + r"[A-Za-z0-9_]{20,}"),
        *[
            re.compile(re.escape(prefix) + r"[A-Za-z0-9_]{20,}")
            for prefix in github_prefixes
        ],
        re.compile(begin_private),
        re.compile(re.escape(aws_prefix) + r"[0-9A-Z]{16}"),
        re.compile(re.escape(slack_prefix) + r"[baprs]-[A-Za-z0-9-]{20,}"),
    ]


def check_versions() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for name, entry in manifest["canonicalDocuments"].items():
        path = ROOT / entry["path"]
        if not path.is_file():
            raise AssertionError(f"{name}: missing {entry['path']}")
        metadata = frontmatter(path)
        if metadata.get("version") != entry["version"]:
            raise AssertionError(
                f"{name}: manifest={entry['version']} frontmatter={metadata.get('version')}"
            )
        if metadata.get("status") != entry["status"]:
            raise AssertionError(
                f"{name}: manifest status={entry['status']} "
                f"frontmatter={metadata.get('status')}"
            )


def check_current_truth() -> None:
    north = (ROOT / "governance/north-star-v1.2.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "governance/global-roadmap-v1.1.md").read_text(encoding="utf-8")
    collaboration = (
        ROOT / "governance/workspace-collaboration-v2.1.md"
    ).read_text(encoding="utf-8")
    fleet = (ROOT / "governance/fleet-division-v1.1.md").read_text(encoding="utf-8")
    architecture = (
        ROOT / "governance/agent-matrix-architecture-v1.0.md"
    ).read_text(encoding="utf-8")
    start = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
    tool_map = (ROOT / "configs/tool-entry-map.md").read_text(encoding="utf-8")
    global_guide = (ROOT / "GLOBAL_AGENT_GUIDE.md").read_text(encoding="utf-8")
    role_matrix = (ROOT / "TOOL_ROLE_MATRIX.md").read_text(encoding="utf-8")
    bootstrap = (ROOT / "BOOTSTRAP_ONE_LINE.md").read_text(encoding="utf-8")
    operating_system = (
        ROOT / "docs/multi-agent-collaboration-operating-system.md"
    ).read_text(encoding="utf-8")
    operating_standard = (
        ROOT / "governance/unified-agent-collaboration-standard.md"
    ).read_text(encoding="utf-8")
    local_usage = (ROOT / "governance/LOCAL-USAGE.md").read_text(encoding="utf-8")
    drift_spec = (
        ROOT / "governance/specs/pi-drift-governance-spec.md"
    ).read_text(encoding="utf-8")
    spec = (
        ROOT / "specs/pi-cognitive-plane-and-self-evolution-v1.0.md"
    ).read_text(encoding="utf-8")

    required = {
        "north-star": [
            "Pi 是经用户授权的 ECS 中央协调者",
            "统一 Trae",
            "唯一战略授权源、T3 决策者与最终裁判",
        ],
        "roadmap": [
            "Pi ECS 已运行采集→反思→记忆→日报闭环",
            "CSM W5.5 数据流仅保留代码与历史证据",
            "统一 Trae 是实现、集成、Git/PR、产品测试和浏览器验收",
        ],
        "collaboration": [
            "Pi 是经用户授权的 ECS 中央协调者",
            "ZCode",
            "统一实现主体",
        ],
        "fleet": [
            "非终端知识吸收",
            "Trae      全栈实现",
            "Pi 提案 → ZCode/Qoder/Mira 评审",
        ],
        "architecture": [
            "Pi ↔ Trae",
            "ZCode(非终端评审)",
            "独立 Solo",
        ],
        "start": [
            "current roster: Pi / unified Trae / ZCode / Qoder / Kimi / Mira",
            "version-manifest",
        ],
        "tool-map": [
            "## Pi",
            "## ZCode",
            "## Unified Trae",
        ],
        "global-guide": [
            "Pi, unified Trae, ZCode, Qoder, Kimi, Mira",
            "natural language grounded in current truth",
        ],
        "role-matrix": [
            "## Pi",
            "## Unified Trae",
            "## ZCode",
            "## Retired roles",
        ],
        "bootstrap": [
            "Pi, unified Trae, ZCode, Qoder, Kimi, Mira",
            "Claude Code and independent Solo are retired",
        ],
        "operating-system": ["状态：historical"],
        "operating-standard": [
            "Pi 无 Git 写权限",
            "Pi 只读检测和协调",
        ],
        "local-usage": [
            "Pi, unified Trae, ZCode, Qoder, Kimi, Mira",
            "原 Trae 与 Solo 已合并为统一 Trae",
        ],
        "drift-spec": [
            "agent/trae-mac",
            "ZCode 非终端",
            "历史 `agent/solo` 不参与活动体检",
        ],
        "self-evolution-spec": [
            "认知自更新质量门",
            "能力自改质量门",
            "原始审计记录永久排除出 Pi 自改白名单",
            "观察 | 记录、聚合、展示、请求补充信息",
            "`baseline`：变更前基线值",
            "任何一项不满足即判失败",
        ],
    }
    documents = {
        "north-star": north,
        "roadmap": roadmap,
        "collaboration": collaboration,
        "fleet": fleet,
        "architecture": architecture,
        "start": start,
        "tool-map": tool_map,
        "global-guide": global_guide,
        "role-matrix": role_matrix,
        "bootstrap": bootstrap,
        "operating-system": operating_system,
        "operating-standard": operating_standard,
        "local-usage": local_usage,
        "drift-spec": drift_spec,
        "self-evolution-spec": spec,
    }
    for name, phrases in required.items():
        for phrase in phrases:
            if phrase not in documents[name]:
                raise AssertionError(f"{name}: missing required truth: {phrase}")

    forbidden = {
        "north-star": ["用户是唯一协调者"],
        "roadmap": [
            "Trae 系只保留 **Trae SOLO 一个独立角色**",
            "W5.5 数据流闭环（横跨 O1/O2",
        ],
        "collaboration": [
            "唯一协调者与最终裁判是用户",
            "Trae SOLO |",
            "深度编程/核心实现 | ZCode",
            "Pi 代劳 push",
            "架构真值 v1.0",
            "代劳 push（授权内）",
        ],
        "architecture": [
            "待ECS实测验证",
            "Pi 直接帮 push",
            "Pi 集成窗口:定期把各分支合并到master",
            "Pi轮询+代劳push",
        ],
        "start": [
            "current roster: ZCode / Qoder / Kimi / Mira / Trae SOLO",
            "north-star: v1.2",
            "roadmap: v1.1",
            "fleet-division: v1.1",
        ],
        "tool-map": ["## Trae SOLO（编队独立角色"],
        "global-guide": ["Trae IDE, Claude Code, Trae SOLO"],
        "role-matrix": ["## Claude Code", "## Trae SOLO PC"],
        "bootstrap": ["Mira, Claude Code, Trae SOLO"],
        "drift-spec": [
            "Pi daemon 在满足 §4.1 全部条件时自动执行",
            "代劳 push（授权后启用）",
        ],
        "operating-standard": ["Pi 代劳 push 例外"],
        "local-usage": ["编队里 Trae 系只保留 SOLO 独立角色"],
    }
    for name, phrases in forbidden.items():
        for phrase in phrases:
            if phrase in documents[name]:
                raise AssertionError(f"{name}: forbidden current truth: {phrase}")


def check_drift_config() -> None:
    path = ROOT / "governance/configs/drift-config.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    aetheris = next(repo for repo in config["repos"] if repo["name"] == "Aetheris")
    expected = [
        "agent/trae-mac",
        "agent/zcode-mac",
        "agent/qoder-mac",
        "agent/kimi-mac",
    ]
    if aetheris["agent_branches"] != expected:
        raise AssertionError(
            f"drift config active branches mismatch: {aetheris['agent_branches']}"
        )
    for retired in ["agent/claude", "agent/solo", "agent/trae", "agent/zcode"]:
        if retired not in config["retired_clones"]:
            raise AssertionError(f"drift config missing retired branch: {retired}")


def check_agent_wiki() -> None:
    root = ROOT / "knowledge/wiki/agents"
    expected_active = ["pi.md", "trae.md", "zcode.md", "qoder.md", "kimi.md", "mira.md"]
    for name in expected_active:
        metadata = frontmatter(root / name)
        if metadata.get("status") != "active":
            raise AssertionError(f"agent wiki should be active: {name}")
    for name in ["claude-code.md", "trae-solo.md"]:
        metadata = frontmatter(root / name)
        if metadata.get("status") != "retired":
            raise AssertionError(f"agent wiki should be retired: {name}")
    active = sorted(
        path.name
        for path in root.glob("*.md")
        if frontmatter(path).get("status") == "active"
    )
    if active != sorted(expected_active):
        raise AssertionError(f"unexpected active agent wiki pages: {active}")


def check_tracked_secrets() -> None:
    patterns = secret_patterns()
    findings: list[str] = []
    for path in tracked_files():
        if not path.is_file():
            continue
        content = path.read_bytes()
        if b"\0" in content:
            continue
        text = content.decode("utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in patterns):
            findings.append(str(path.relative_to(ROOT)))
    if findings:
        raise AssertionError(
            "tracked credential pattern in: " + ", ".join(sorted(findings))
        )


def main() -> int:
    try:
        check_versions()
        check_current_truth()
        check_drift_config()
        check_agent_wiki()
        check_tracked_secrets()
    except (AssertionError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"[governance-truth] FAIL: {error}", file=sys.stderr)
        return 1
    print("[governance-truth] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
