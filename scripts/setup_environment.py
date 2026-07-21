from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


PLACEHOLDER = "<AGENT_SPEC_REPOSITORY_PATH>"
REQUIRED_REFERENCES = (
    "instructions/core/principles.md",
    "instructions/core/task-lifecycle.md",
    "docs/MAINTENANCE.md",
)


@dataclass(frozen=True)
class Result:
    status: str
    step: str
    path: str
    message: str


def default_root_agents() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    return base / "AGENTS.md"


def normalized(value: str) -> str:
    return value.replace("\\", "/").rstrip("/").casefold()


def run_json(command: list[str], cwd: Path) -> tuple[int, dict[str, object] | None, str]:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = None
    detail = (result.stderr or result.stdout).strip()
    return result.returncode, payload, detail


def validate_repository(repo: Path) -> Result:
    script = repo / "scripts" / "validate_repository.py"
    if not script.is_file():
        return Result("FAIL", "repository", str(script), "repo検証スクリプトがありません")
    code, payload, detail = run_json(
        [sys.executable, str(script), "--repo", str(repo), "--json"], repo
    )
    if code != 0 or not isinstance(payload, dict):
        return Result("FAIL", "repository", str(repo), f"repo検証に失敗しました: {detail}")
    return Result(
        "PASS",
        "repository",
        str(repo),
        f"repo検証成功、warnings={payload.get('warnings', 0)}",
    )


def template_path(repo: Path, profile: str) -> Path:
    if profile == "personal":
        return repo / "ROOT_AGENTS_TEMPLATE.md"
    return repo / "templates" / "ROOT_AGENTS_GENERIC.md"


def root_agents_compatible(text: str, repo: Path, profile: str) -> bool:
    if PLACEHOLDER in text or normalized(str(repo)) not in normalized(text):
        return False
    if any(reference not in text for reference in REQUIRED_REFERENCES):
        return False
    return profile != "personal" or "profiles/personal/AGENTS.md" in text


def prepare_root_agents(
    repo: Path, destination: Path, profile: str, apply: bool
) -> Result:
    source = template_path(repo, profile)
    if not source.is_file():
        return Result("FAIL", "root-agents", str(source), "ルートAGENTSテンプレートがありません")
    try:
        template = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        return Result("FAIL", "root-agents", str(source), f"テンプレートを読めません: {error}")
    if PLACEHOLDER not in template:
        return Result("FAIL", "root-agents", str(source), "repoパスのプレースホルダーがありません")
    rendered = template.replace(PLACEHOLDER, str(repo))

    if destination.exists():
        if not destination.is_file():
            return Result("FAIL", "root-agents", str(destination), "同名パスがファイルではありません")
        try:
            existing = destination.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as error:
            return Result("FAIL", "root-agents", str(destination), f"既存ファイルを読めません: {error}")
        if existing == rendered or root_agents_compatible(existing, repo, profile):
            return Result("PASS", "root-agents", str(destination), "互換性のある既存ファイルを保持します")
        return Result(
            "FAIL",
            "root-agents",
            str(destination),
            "既存ファイルは必要な参照を満たしません。自動上書きせず、テンプレートを手動統合してください",
        )

    if not apply:
        return Result(
            "PLAN",
            "root-agents",
            str(destination),
            f"{source.name}から生成予定です。変更するには--applyを付けて再実行してください",
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8", newline="\n") as output:
            output.write(rendered)
    except OSError as error:
        return Result("FAIL", "root-agents", str(destination), f"作成に失敗しました: {error}")
    return Result("PASS", "root-agents", str(destination), f"{source.name}から生成しました")


def install_skills(
    repo: Path, target: Path, mode: str, apply: bool
) -> list[Result]:
    script = repo / "scripts" / "install_skills.py"
    if not script.is_file():
        return [Result("FAIL", "skills", str(script), "Skill導入スクリプトがありません")]
    command = [
        sys.executable,
        str(script),
        "--repo",
        str(repo),
        "--target",
        str(target),
        "--mode",
        mode,
        "--json",
    ]
    if apply:
        command.append("--apply")
    code, payload, detail = run_json(command, repo)
    if payload is None or not isinstance(payload.get("results"), list):
        return [Result("FAIL", "skills", str(target), f"Skill導入結果を読めません: {detail}")]
    results = [
        Result(
            str(item.get("status", "FAIL")),
            f"skill:{item.get('skill', '-')}",
            str(item.get("destination", target)),
            str(item.get("message", "結果がありません")),
        )
        for item in payload["results"]
        if isinstance(item, dict)
    ]
    if code != 0 and not any(item.status == "FAIL" for item in results):
        results.append(Result("FAIL", "skills", str(target), detail or f"終了コード {code}"))
    return results


def verify_setup(repo: Path, root_agents: Path, skills_target: Path, profile: str) -> Result:
    script = repo / "skills" / "verify-agent-spec-setup" / "scripts" / "verify_setup.py"
    if not script.is_file():
        return Result("FAIL", "verification", str(script), "セットアップ検証スクリプトがありません")
    command = [
        sys.executable,
        str(script),
        "--repo",
        str(repo),
        "--root-agents",
        str(root_agents),
        "--installed-skills-dir",
        str(skills_target),
        "--require-skills",
        "--json",
    ]
    if profile == "personal":
        command.extend(("--expect-profile", "personal"))
    code, payload, detail = run_json(command, repo)
    if code != 0 or not isinstance(payload, dict):
        return Result("FAIL", "verification", str(repo), f"セットアップ検証に失敗しました: {detail}")
    counts = payload.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    return Result(
        "PASS",
        "verification",
        str(repo),
        f"pass={counts.get('PASS', 0)} warn={counts.get('WARN', 0)} fail={counts.get('FAIL', 0)}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="agent-specのルートAGENTSとSkillを安全にセットアップして検証します。"
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="agent-specのルート")
    parser.add_argument("--profile", choices=("personal", "generic"), default="personal")
    parser.add_argument("--root-agents", type=Path, default=default_root_agents())
    parser.add_argument(
        "--skills-target", type=Path, default=Path.home() / ".agents" / "skills"
    )
    parser.add_argument("--skill-mode", choices=("auto", "symlink", "copy"), default="auto")
    parser.add_argument("--apply", action="store_true", help="実際に変更する。省略時はdry-run")
    parser.add_argument("--json", action="store_true", help="JSONで出力する")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    root_agents = args.root_agents.expanduser().resolve()
    skills_target = args.skills_target.expanduser().resolve()
    skill_mode = args.skill_mode
    if skill_mode == "auto":
        skill_mode = "copy" if os.name == "nt" else "symlink"

    results = [validate_repository(repo)]
    if not any(item.status == "FAIL" for item in results):
        results.append(prepare_root_agents(repo, root_agents, args.profile, args.apply))
    if not any(item.status == "FAIL" for item in results):
        results.extend(install_skills(repo, skills_target, skill_mode, args.apply))
    if args.apply and not any(item.status == "FAIL" for item in results):
        results.append(verify_setup(repo, root_agents, skills_target, args.profile))

    counts = {
        status: sum(item.status == status for item in results)
        for status in ("PASS", "PLAN", "FAIL")
    }
    payload = {
        "repo": str(repo),
        "profile": args.profile,
        "root_agents": str(root_agents),
        "skills_target": str(skills_target),
        "skill_mode": skill_mode,
        "apply": args.apply,
        "counts": counts,
        "results": [asdict(item) for item in results],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"[{item.status}] {item.step}: {item.path}: {item.message}")
        print(
            f"SUMMARY: pass={counts['PASS']} plan={counts['PLAN']} fail={counts['FAIL']}"
        )
        if not args.apply and counts["FAIL"] == 0:
            print("NEXT: 内容を確認し、同じコマンドへ--applyを付けて再実行してください")
        elif args.apply and counts["FAIL"] == 0:
            print("NEXT: Codexを再起動するか、新しいタスクでAGENTS実在パスとSkill一覧を確認してください")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
