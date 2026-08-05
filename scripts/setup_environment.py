from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


PLACEHOLDER = "<AGENT_SPEC_REPOSITORY_PATH>"
OPTIMIZED_COMMON_REFERENCES = (
    "instructions/core/principles.md",
    "instructions/core/task-lifecycle.md",
    "instructions/core/instruction-authoring.md",
    "instructions/use-cases/code-change.md",
    "instructions/use-cases/code-review.md",
    "instructions/use-cases/research.md",
    "instructions/use-cases/README.md",
    "adapters/README.md",
    "docs/MAINTENANCE.md",
    "docs/SKILL_MANAGEMENT.md",
)
OPTIMIZED_PERSONAL_REFERENCES = (
    "profiles/personal/unity-csharp.md",
    "profiles/personal/web-development.md",
    "profiles/personal/project-recording.md",
    "profiles/personal/mcp-and-voicevox.md",
)
LEGACY_COMMON_REFERENCES = (
    "instructions/core/principles.md",
    "instructions/core/task-lifecycle.md",
    "docs/MAINTENANCE.md",
)
BACKUP_SUFFIX = ".pre-token-efficiency.bak"


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


def root_agents_compatibility(text: str, repo: Path, profile: str) -> str | None:
    if PLACEHOLDER in text or normalized(str(repo)) not in normalized(text):
        return None
    optimized = OPTIMIZED_COMMON_REFERENCES
    if profile == "personal":
        optimized += OPTIMIZED_PERSONAL_REFERENCES
    optimized_profile_ok = profile == "personal" or "profiles/personal/" not in text
    if optimized_profile_ok and all(reference in text for reference in optimized):
        return "optimized"
    if profile == "personal":
        legacy_profile_ok = "profiles/personal/AGENTS.md" in text
    else:
        legacy_profile_ok = "profiles/personal/" not in text
    legacy_use_cases = "instructions/use-cases/" in text
    legacy_chain = "タスク開始時に" in text
    if (
        legacy_profile_ok
        and legacy_use_cases
        and legacy_chain
        and all(reference in text for reference in LEGACY_COMMON_REFERENCES)
    ):
        return "legacy"
    return None


def next_backup_path(destination: Path) -> Path:
    base = destination.with_name(destination.name + BACKUP_SUFFIX)
    if not base.exists():
        return base
    for index in range(1, 10_000):
        candidate = destination.with_name(f"{destination.name}{BACKUP_SUFFIX}.{index}")
        if not candidate.exists():
            return candidate
    raise OSError("利用可能なバックアップ名を確保できません")


def migrate_legacy_root_agents(destination: Path, rendered: str) -> Path:
    backup = next_backup_path(destination)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            output.write(rendered)
            output.flush()
            os.fsync(output.fileno())
            temporary = Path(output.name)
        shutil.copymode(destination, temporary)
        shutil.copy2(destination, backup)
        os.replace(temporary, destination)
    except OSError:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    return backup


def prepare_root_agents(
    repo: Path,
    destination: Path,
    profile: str,
    apply: bool,
    migrate_legacy: bool,
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

    if destination.is_symlink():
        return Result(
            "FAIL",
            "root-agents",
            str(destination),
            "既存ルートAGENTSがシンボリックリンクのため自動移行しません",
        )
    if destination.exists():
        if not destination.is_file():
            return Result("FAIL", "root-agents", str(destination), "同名パスがファイルではありません")
        try:
            existing = destination.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as error:
            return Result("FAIL", "root-agents", str(destination), f"既存ファイルを読めません: {error}")
        compatibility = root_agents_compatibility(existing, repo, profile)
        if existing == rendered or compatibility == "optimized":
            return Result("PASS", "root-agents", str(destination), "最適化済みの既存ファイルを保持します")
        if compatibility == "legacy":
            if migrate_legacy and not apply:
                return Result(
                    "PLAN",
                    "root-agents",
                    str(destination),
                    f"旧ルーターを{destination.name + BACKUP_SUFFIX}系の名前へバックアップして最適化版へ移行予定です",
                )
            if migrate_legacy:
                try:
                    backup = migrate_legacy_root_agents(destination, rendered)
                except OSError as error:
                    return Result(
                        "FAIL",
                        "root-agents",
                        str(destination),
                        f"旧ルーターの移行に失敗しました: {error}",
                    )
                return Result(
                    "PASS",
                    "root-agents",
                    str(destination),
                    f"旧ルーターを最適化版へ移行しました。バックアップ: {backup}",
                )
            return Result(
                "PASS",
                "root-agents",
                str(destination),
                "旧ルーターとの読取互換性があるため保持します。トークン効率化には新テンプレートを手動統合してください",
            )
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
    command.extend(("--expect-profile", profile))
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
    parser.add_argument(
        "--migrate-root-agents",
        action="store_true",
        help="読取互換の旧ルートAGENTSをバックアップして最適化版へ移行する",
    )
    parser.add_argument("--apply", action="store_true", help="実際に変更する。省略時はdry-run")
    parser.add_argument("--json", action="store_true", help="JSONで出力する")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    root_agents = args.root_agents.expanduser().absolute()
    skills_target = args.skills_target.expanduser().resolve()
    skill_mode = args.skill_mode
    if skill_mode == "auto":
        skill_mode = "copy" if os.name == "nt" else "symlink"

    results = [validate_repository(repo)]
    if not any(item.status == "FAIL" for item in results):
        results.append(
            prepare_root_agents(
                repo,
                root_agents,
                args.profile,
                args.apply,
                args.migrate_root_agents,
            )
        )
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
        "migrate_root_agents": args.migrate_root_agents,
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
