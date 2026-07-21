from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


TEXT_EXTENSIONS = {".json", ".md", ".py", ".toml", ".yaml", ".yml"}
REQUIRED_PATHS = (
    "AGENTS.md",
    "README.md",
    "docs/MAINTENANCE.md",
    "docs/SKILL_MANAGEMENT.md",
    "instructions/core/principles.md",
    "instructions/core/task-lifecycle.md",
    "scripts/validate_skills.py",
    "skills/README.md",
)
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
MEMORY_PATTERN = re.compile(r"mem:([a-zA-Z0-9_-]+)")
MACHINE_PATH_PATTERNS = (
    re.compile(r"\b[A-Za-z]:[\\/](?:Users|Develop)[\\/]", re.IGNORECASE),
    re.compile(r"/(?:Users|home)/[^/\s]+/"),
)


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    path: str
    message: str


def repository_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        if relative.as_posix() == ".serena/project.local.yml":
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS:
            files.append(path)
    return sorted(files)


def read_utf8(path: Path) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8-sig"), None
    except (OSError, UnicodeDecodeError) as error:
        return None, str(error)


def validate_text_file(root: Path, path: Path, text: str) -> list[Issue]:
    issues: list[Issue] = []
    relative = path.relative_to(root).as_posix()
    for number, line in enumerate(text.splitlines(), start=1):
        if line.endswith((" ", "\t")):
            issues.append(Issue("ERROR", "trailing-whitespace", relative, f"{number}行目"))
        if line.startswith(("<<<<<<<", "=======", ">>>>>>>")):
            issues.append(Issue("ERROR", "conflict-marker", relative, f"{number}行目"))

    if path.suffix.lower() != ".py":
        for pattern in MACHINE_PATH_PATTERNS:
            match = pattern.search(text)
            if match:
                issues.append(
                    Issue("ERROR", "machine-path", relative, f"端末固有パスを検出: {match.group(0)}")
                )
    return issues


def validate_markdown_links(root: Path, path: Path, text: str) -> list[Issue]:
    issues: list[Issue] = []
    relative = path.relative_to(root).as_posix()
    for match in LINK_PATTERN.finditer(text):
        target = match.group(1).strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        if not target or re.match(r"^(?:https?://|mailto:|#)", target):
            continue
        target = target.split("#", 1)[0].split("?", 1)[0]
        if not target:
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            issues.append(Issue("ERROR", "broken-link", relative, target))
    return issues


def validate_memory_references(root: Path, markdown: list[tuple[Path, str]]) -> list[Issue]:
    issues: list[Issue] = []
    memory_root = root / ".serena" / "memories"
    memories = {path.stem for path in memory_root.glob("*.md")} if memory_root.is_dir() else set()
    for path, text in markdown:
        relative = path.relative_to(root).as_posix()
        for match in MEMORY_PATTERN.finditer(text):
            if match.group(1) not in memories:
                issues.append(Issue("ERROR", "missing-memory", relative, match.group(1)))
    return issues


def run_command_check(root: Path, command: list[str], code: str) -> list[Issue]:
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    except OSError as error:
        return [Issue("WARN", code, ".", f"実行できません: {error}")]
    if result.returncode == 0:
        return []
    detail = (result.stderr or result.stdout).strip()
    return [Issue("ERROR", code, ".", detail or f"終了コード {result.returncode}")]


def validate_repository(root: Path) -> tuple[list[Issue], int, int]:
    issues: list[Issue] = []
    for required in REQUIRED_PATHS:
        if not (root / required).exists():
            issues.append(Issue("ERROR", "missing-required-path", required, "必須パスがありません"))

    files = repository_files(root)
    markdown: list[tuple[Path, str]] = []
    for path in files:
        text, error = read_utf8(path)
        relative = path.relative_to(root).as_posix()
        if error:
            issues.append(Issue("ERROR", "invalid-utf8", relative, error))
            continue
        assert text is not None
        issues.extend(validate_text_file(root, path, text))
        if path.suffix.lower() == ".md":
            markdown.append((path, text))
            issues.extend(validate_markdown_links(root, path, text))

    issues.extend(validate_memory_references(root, markdown))
    skill_validator = root / "scripts" / "validate_skills.py"
    if skill_validator.is_file():
        issues.extend(
            run_command_check(root, [sys.executable, str(skill_validator)], "skill-validation")
        )
    issues.extend(run_command_check(root, ["git", "diff", "--check"], "git-diff-check"))
    return issues, len(files), len(markdown)


def main() -> int:
    parser = argparse.ArgumentParser(description="agent-specリポジトリ全体を検証します。")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="agent-specのルート")
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    args = parser.parse_args()

    root = args.repo.expanduser().resolve()
    issues, text_count, markdown_count = validate_repository(root)
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    warnings = [issue for issue in issues if issue.severity == "WARN"]

    if args.json:
        print(
            json.dumps(
                {
                    "repo": str(root),
                    "text_files": text_count,
                    "markdown_files": markdown_count,
                    "errors": len(errors),
                    "warnings": len(warnings),
                    "issues": [asdict(issue) for issue in issues],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for issue in issues:
            print(f"[{issue.severity}] {issue.code}: {issue.path}: {issue.message}")
        print(
            f"SUMMARY: errors={len(errors)} warnings={len(warnings)} "
            f"text={text_count} markdown={markdown_count}"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
