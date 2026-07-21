from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FORBIDDEN_FILES = {
    "CHANGELOG.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "README.md",
}


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    except UnicodeDecodeError as error:
        return {}, [f"{path}: UTF-8として読めません: {error}"]

    if not text.startswith("---\n"):
        return {}, [f"{path}: YAML frontmatterの開始区切りがありません"]

    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, [f"{path}: YAML frontmatterの終了区切りがありません"]

    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"{path}: frontmatterを解釈できません: {line}")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in values:
            errors.append(f"{path}: frontmatterキーが重複しています: {key}")
        values[key] = unquote(value.strip())
    return values, errors


def yaml_string(text: str, key: str) -> str | None:
    pattern = rf"^\s+{re.escape(key)}:\s+[\"'](.+)[\"']\s*$"
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1) if match else None


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill_dir}: SKILL.mdがありません"]

    metadata, parse_errors = parse_frontmatter(skill_md)
    errors.extend(parse_errors)
    extra_keys = sorted(set(metadata) - {"name", "description"})
    missing_keys = sorted({"name", "description"} - set(metadata))
    if extra_keys:
        errors.append(f"{skill_md}: 許可されていないfrontmatterキー: {', '.join(extra_keys)}")
    if missing_keys:
        errors.append(f"{skill_md}: 必須frontmatterキーがありません: {', '.join(missing_keys)}")

    name = metadata.get("name", "")
    if name and not NAME_PATTERN.fullmatch(name):
        errors.append(f"{skill_md}: nameはlowercase kebab-caseにしてください: {name}")
    if name and len(name) >= 64:
        errors.append(f"{skill_md}: nameは64文字未満にしてください")
    if name and name != skill_dir.name:
        errors.append(f"{skill_md}: nameとディレクトリ名が一致しません: {name} != {skill_dir.name}")
    if not metadata.get("description", "").strip():
        errors.append(f"{skill_md}: descriptionが空です")

    for forbidden in sorted(FORBIDDEN_FILES):
        if (skill_dir / forbidden).exists():
            errors.append(f"{skill_dir / forbidden}: Skill内ではなくrepo側文書へ移してください")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.is_file():
        try:
            yaml_text = openai_yaml.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as error:
            errors.append(f"{openai_yaml}: UTF-8として読めません: {error}")
            return errors

        display_name = yaml_string(yaml_text, "display_name")
        short_description = yaml_string(yaml_text, "short_description")
        default_prompt = yaml_string(yaml_text, "default_prompt")
        if not display_name:
            errors.append(f"{openai_yaml}: interface.display_nameがありません")
        if not short_description:
            errors.append(f"{openai_yaml}: interface.short_descriptionがありません")
        elif not 25 <= len(short_description) <= 64:
            errors.append(f"{openai_yaml}: short_descriptionは25〜64文字にしてください")
        if not default_prompt:
            errors.append(f"{openai_yaml}: interface.default_promptがありません")
        elif name and f"${name}" not in default_prompt:
            errors.append(f"{openai_yaml}: default_promptに${name}を含めてください")

    return errors


def main() -> int:
    if not SKILLS_ROOT.is_dir():
        print(f"ERROR: Skillルートがありません: {SKILLS_ROOT}", file=sys.stderr)
        return 1

    skill_dirs = sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir())
    if not skill_dirs:
        print("ERROR: 管理対象Skillがありません", file=sys.stderr)
        return 1

    errors = [error for skill_dir in skill_dirs for error in validate_skill(skill_dir)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(skill_dirs)}件のSkillを検証しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
