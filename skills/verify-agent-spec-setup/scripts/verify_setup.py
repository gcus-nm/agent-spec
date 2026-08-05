from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


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


@dataclass(frozen=True)
class Finding:
    status: str
    code: str
    path: str
    message: str


def default_repo() -> Path:
    current = Path.cwd()
    if (current / "docs" / "SKILL_MANAGEMENT.md").is_file():
        return current
    bundled = Path(__file__).resolve().parents[3]
    if (bundled / "docs" / "SKILL_MANAGEMENT.md").is_file():
        return bundled
    return current


def default_root_agents() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    return base / "AGENTS.md"


def read_utf8(path: Path) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8-sig"), None
    except (OSError, UnicodeDecodeError) as error:
        return None, str(error)


def normalized(value: str) -> str:
    return value.replace("\\", "/").rstrip("/").casefold()


def directory_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(item for item in path.rglob("*") if item.is_file()):
        relative = file.relative_to(path)
        if "__pycache__" in relative.parts or file.suffix.lower() in {".pyc", ".pyo"}:
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def install_command(repo: Path, installed_root: Path) -> str:
    interpreter = "python" if os.name == "nt" else "python3"
    mode = "copy" if os.name == "nt" else "symlink"
    script = repo / "scripts" / "install_skills.py"
    return (
        f'{interpreter} "{script}" --repo "{repo}" '
        f'--target "{installed_root}" --mode {mode} --apply'
    )


def repository_check(repo: Path) -> Finding:
    validator = repo / "scripts" / "validate_repository.py"
    if not validator.is_file():
        return Finding("FAIL", "repo-validator-missing", str(validator), "検証スクリプトがありません")
    result = subprocess.run(
        [sys.executable, str(validator), "--repo", str(repo), "--json"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = None
    if result.returncode != 0:
        detail = payload if payload is not None else (result.stderr or result.stdout).strip()
        return Finding("FAIL", "repo-validation", str(repo), f"repo検証に失敗: {detail}")
    warnings = payload.get("warnings", 0) if isinstance(payload, dict) else 0
    return Finding("PASS", "repo-validation", str(repo), f"repo検証成功、warnings={warnings}")


def check_root_agents(repo: Path, path: Path, expect_profile: str | None) -> list[Finding]:
    if not path.is_file():
        return [Finding("FAIL", "root-agents-missing", str(path), "ルートAGENTS.mdがありません")]
    text, error = read_utf8(path)
    if error or text is None:
        return [Finding("FAIL", "root-agents-utf8", str(path), error or "読込失敗")]

    findings = [Finding("PASS", "root-agents-readable", str(path), "UTF-8で読めます")]
    if "<AGENT_SPEC_REPOSITORY_PATH>" in text:
        findings.append(
            Finding("FAIL", "root-agents-placeholder", str(path), "repoパスが未置換です")
        )
    else:
        findings.append(Finding("PASS", "root-agents-placeholder", str(path), "repoパス置換済み"))

    optimized_references = OPTIMIZED_COMMON_REFERENCES
    if expect_profile == "personal":
        optimized_references += OPTIMIZED_PERSONAL_REFERENCES
    optimized_profile_ok = expect_profile != "generic" or "profiles/personal/" not in text
    optimized = optimized_profile_ok and all(
        reference in text for reference in optimized_references
    )
    if expect_profile == "personal":
        legacy_profile_ok = "profiles/personal/AGENTS.md" in text
    elif expect_profile == "generic":
        legacy_profile_ok = "profiles/personal/" not in text
    else:
        legacy_profile_ok = True
    legacy_use_cases = "instructions/use-cases/" in text
    legacy_chain = "タスク開始時に" in text
    legacy = legacy_profile_ok and legacy_use_cases and legacy_chain and all(
        reference in text for reference in LEGACY_COMMON_REFERENCES
    )

    if optimized:
        findings.append(
            Finding("PASS", "root-agents-routing", str(path), "条件付き直接ルーティングを確認しました")
        )
    elif legacy:
        findings.append(
            Finding(
                "WARN",
                "root-agents-legacy-routing",
                str(path),
                "旧ルーターは読取互換です。トークン効率化には新テンプレートを手動統合してください",
            )
        )
    else:
        missing = [reference for reference in optimized_references if reference not in text]
        findings.append(
            Finding(
                "FAIL",
                "root-agents-routing",
                str(path),
                f"最適化済みまたは旧互換のルーティングではありません。不足: {', '.join(missing)}",
            )
        )

    if expect_profile:
        profile_reference = f"profiles/{expect_profile}/AGENTS.md"
        if expect_profile == "personal":
            profile_ok = optimized or profile_reference in text
        elif expect_profile == "generic":
            profile_ok = optimized and "profiles/personal/" not in text
        else:
            profile_ok = profile_reference in text
        status = "PASS" if profile_ok else "FAIL"
        message = "プロファイル固有ルートあり" if status == "PASS" else "期待するプロファイルルートがありません"
        findings.append(Finding(status, "root-agents-profile", str(path), message))

    if normalized(str(repo.resolve())) in normalized(text):
        findings.append(Finding("PASS", "root-agents-repo-path", str(path), "実際のrepoパスを参照"))
    else:
        findings.append(
            Finding(
                "WARN",
                "root-agents-repo-path",
                str(path),
                "実際のrepoパス文字列を確認できません。別名・シンボリックリンクなら手動確認してください",
            )
        )
    return findings


def check_installed_skills(
    repo: Path, installed_roots: list[Path], require_skills: bool
) -> list[Finding]:
    findings: list[Finding] = []
    source_root = repo / "skills"
    expected_skills = sorted(
        path.name for path in source_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    ) if source_root.is_dir() else []
    if not expected_skills:
        return [Finding("FAIL", "source-skills-empty", str(source_root), "正本Skillがありません")]
    missing_status = "FAIL" if require_skills else "WARN"
    for installed_root in installed_roots:
        installed_root = installed_root.expanduser().resolve()
        if not installed_root.is_dir():
            findings.append(
                Finding(
                    missing_status,
                    "skills-root-missing",
                    str(installed_root),
                    f"Skill導入先がありません。明示的な導入が必要です: "
                    f"{install_command(repo, installed_root)}",
                )
            )
            continue
        for name in expected_skills:
            source = source_root / name
            destination = installed_root / name
            if not source.is_dir():
                findings.append(Finding("FAIL", "source-skill-missing", str(source), "正本Skillがありません"))
                continue
            if not destination.is_dir():
                findings.append(
                    Finding(
                        missing_status,
                        "installed-skill-missing",
                        str(destination),
                        f"導入されていません: {install_command(repo, installed_root)}",
                    )
                )
                continue
            if source.resolve() == destination.resolve():
                findings.append(
                    Finding("PASS", "installed-skill-linked", str(destination), "正本を直接参照しています")
                )
                continue
            try:
                synchronized = directory_digest(source) == directory_digest(destination)
            except OSError as error:
                findings.append(Finding("FAIL", "installed-skill-read", str(destination), str(error)))
                continue
            if synchronized:
                findings.append(
                    Finding("PASS", "installed-skill-synced", str(destination), "正本と内容が一致します")
                )
            else:
                findings.append(
                    Finding(
                        missing_status,
                        "installed-skill-stale",
                        str(destination),
                        "正本と内容が異なります。自動上書きせず差分を確認してから再導入してください: "
                        f"{install_command(repo, installed_root)}",
                    )
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="agent-specのセットアップを読み取り専用で検証します。")
    parser.add_argument("--repo", type=Path, default=default_repo(), help="agent-specのルート")
    parser.add_argument("--root-agents", type=Path, default=default_root_agents(), help="環境ルートAGENTS.md")
    parser.add_argument(
        "--installed-skills-dir",
        type=Path,
        action="append",
        default=[],
        help="Skill導入先。複数回指定できます",
    )
    parser.add_argument("--expect-profile", help="期待するprofiles/<name>/AGENTS.md")
    parser.add_argument("--require-skills", action="store_true", help="Skill未導入・不一致をFAILにする")
    parser.add_argument("--skip-root-agents", action="store_true", help="ルートAGENTS検証を省略する")
    parser.add_argument("--json", action="store_true", help="JSONで出力する")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    findings = [repository_check(repo)]
    if not args.skip_root_agents:
        findings.extend(check_root_agents(repo, args.root_agents.expanduser().resolve(), args.expect_profile))

    installed_roots = list(args.installed_skills_dir)
    if not installed_roots:
        installed_roots = [Path.home() / ".agents" / "skills"]
    findings.extend(check_installed_skills(repo, installed_roots, args.require_skills))

    counts = {status: sum(item.status == status for item in findings) for status in ("PASS", "WARN", "FAIL")}
    if args.json:
        print(
            json.dumps(
                {
                    "repo": str(repo),
                    "counts": counts,
                    "findings": [asdict(item) for item in findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for item in findings:
            print(f"[{item.status}] {item.code}: {item.path}: {item.message}")
        print(f"SUMMARY: pass={counts['PASS']} warn={counts['WARN']} fail={counts['FAIL']}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
