from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


BACKUP_DIRECTORY_SUFFIX = ".pre-refresh-backups"
BACKUP_SUFFIX = ".pre-refresh.bak"


@dataclass(frozen=True)
class Result:
    status: str
    skill: str
    source: str
    destination: str
    message: str


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


def discover_skills(repo: Path) -> list[Path]:
    source_root = repo / "skills"
    if not source_root.is_dir():
        return []
    return sorted(
        path for path in source_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    )


def inspect_existing(source: Path, destination: Path) -> Result | None:
    if destination.is_symlink():
        try:
            if destination.resolve(strict=True) == source.resolve(strict=True):
                return Result(
                    "PASS",
                    source.name,
                    str(source),
                    str(destination),
                    "正本へのシンボリックリンクです",
                )
        except OSError:
            pass
        return Result(
            "FAIL",
            source.name,
            str(source),
            str(destination),
            "既存のシンボリックリンクが別の場所を指しています。内容を確認して手動で整理してください",
        )
    if not destination.exists():
        return None
    if not destination.is_dir():
        return Result(
            "FAIL",
            source.name,
            str(source),
            str(destination),
            "導入先に同名のファイルがあります。内容を確認して手動で整理してください",
        )
    try:
        synchronized = directory_digest(source) == directory_digest(destination)
    except OSError as error:
        return Result("FAIL", source.name, str(source), str(destination), f"比較できません: {error}")
    if synchronized:
        return Result(
            "PASS",
            source.name,
            str(source),
            str(destination),
            "コピー済みで正本と内容が一致します",
        )
    return Result(
        "FAIL",
        source.name,
        str(source),
        str(destination),
        "既存コピーが正本と異なります。自動上書きせず、差分を確認して手動で整理してください",
    )


def next_backup_path(destination: Path) -> Path:
    backup_root = destination.parent.with_name(
        destination.parent.name + BACKUP_DIRECTORY_SUFFIX
    )
    base = backup_root / (destination.name + BACKUP_SUFFIX)
    if not base.exists():
        return base
    for index in range(1, 10_000):
        candidate = backup_root / f"{destination.name}{BACKUP_SUFFIX}.{index}"
        if not candidate.exists():
            return candidate
    raise OSError("利用可能なバックアップ名を確保できません")


def refresh_copy(source: Path, destination: Path, apply: bool) -> Result:
    try:
        backup = next_backup_path(destination)
    except (OSError, ValueError) as error:
        return Result(
            "FAIL",
            source.name,
            str(source),
            str(destination),
            f"更新準備に失敗しました: {error}",
        )
    if not apply:
        return Result(
            "PLAN",
            source.name,
            str(source),
            str(destination),
            f"既存コピーを{backup}へバックアップして正本で更新予定です",
        )

    backup_root = backup.parent
    moved_existing = False
    try:
        backup_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=f".{destination.name}.refresh.", dir=backup_root
        ) as temporary_root:
            staged = Path(temporary_root) / destination.name
            shutil.copytree(source, staged)
            destination.rename(backup)
            moved_existing = True
            try:
                staged.rename(destination)
            except OSError as install_error:
                try:
                    backup.rename(destination)
                    moved_existing = False
                except OSError as restore_error:
                    return Result(
                        "FAIL",
                        source.name,
                        str(source),
                        str(destination),
                        "更新と復元に失敗しました: "
                        f"更新={install_error}; 復元={restore_error}; バックアップ={backup}",
                    )
                return Result(
                    "FAIL",
                    source.name,
                    str(source),
                    str(destination),
                    f"更新に失敗したため既存コピーを復元しました: {install_error}",
                )
    except OSError as error:
        if moved_existing:
            return Result(
                "FAIL",
                source.name,
                str(source),
                str(destination),
                "更新に失敗しました。"
                f"既存コピーのバックアップ: {backup}; エラー: {error}",
            )
        return Result(
            "FAIL",
            source.name,
            str(source),
            str(destination),
            f"更新に失敗しました: {error}",
        )
    return Result(
        "PASS",
        source.name,
        str(source),
        str(destination),
        f"既存コピーを正本で更新しました。バックアップ: {backup}",
    )


def install_skill(
    source: Path,
    destination: Path,
    mode: str,
    apply: bool,
    refresh_existing: bool,
) -> Result:
    existing = inspect_existing(source, destination)
    if existing is not None:
        if (
            refresh_existing
            and existing.status == "FAIL"
            and mode == "copy"
            and not destination.is_symlink()
            and destination.is_dir()
        ):
            try:
                directory_digest(source)
                directory_digest(destination)
            except OSError as error:
                return Result(
                    "FAIL",
                    source.name,
                    str(source),
                    str(destination),
                    f"更新前に比較できません: {error}",
                )
            return refresh_copy(source, destination, apply)
        return existing
    if not apply:
        return Result(
            "PLAN",
            source.name,
            str(source),
            str(destination),
            f"{mode}で導入予定です。変更するには--applyを付けて再実行してください",
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if mode == "symlink":
            destination.symlink_to(source.resolve(), target_is_directory=True)
        else:
            shutil.copytree(source, destination)
    except OSError as error:
        return Result("FAIL", source.name, str(source), str(destination), f"導入に失敗しました: {error}")
    return Result(
        "PASS",
        source.name,
        str(source),
        str(destination),
        f"{mode}で導入しました",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="agent-specで管理するSkillを安全にコピーまたはシンボリックリンクします。"
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="agent-specのルート")
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.home() / ".agents" / "skills",
        help="Skill導入先ディレクトリ",
    )
    parser.add_argument("--mode", choices=("symlink", "copy"), default="symlink")
    parser.add_argument(
        "--refresh-existing",
        action="store_true",
        help="正本と異なる既存Skillコピーをバックアップして更新する",
    )
    parser.add_argument("--apply", action="store_true", help="実際に導入する。省略時はdry-run")
    parser.add_argument("--json", action="store_true", help="JSONで出力する")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    target = args.target.expanduser().resolve()
    skills = discover_skills(repo)
    if not skills:
        results = [
            Result("FAIL", "-", str(repo / "skills"), str(target), "導入可能なSkillがありません")
        ]
    elif target.exists() and not target.is_dir():
        results = [
            Result("FAIL", "-", str(repo / "skills"), str(target), "導入先がディレクトリではありません")
        ]
    else:
        results = [
            install_skill(
                source,
                target / source.name,
                args.mode,
                args.apply,
                args.refresh_existing,
            )
            for source in skills
        ]

    counts = {
        status: sum(result.status == status for result in results)
        for status in ("PASS", "PLAN", "FAIL")
    }
    if args.json:
        print(
            json.dumps(
                {
                    "repo": str(repo),
                    "target": str(target),
                    "mode": args.mode,
                    "refresh_existing": args.refresh_existing,
                    "apply": args.apply,
                    "counts": counts,
                    "results": [asdict(result) for result in results],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for result in results:
            print(f"[{result.status}] {result.skill}: {result.destination}: {result.message}")
        print(
            f"SUMMARY: pass={counts['PASS']} plan={counts['PLAN']} fail={counts['FAIL']}"
        )
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
