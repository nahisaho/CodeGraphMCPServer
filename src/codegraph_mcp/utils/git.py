"""
Git Operations Utility
======================

Git変更検出とファイル操作を提供します。
REQ-STR-004: Git連携によるインクリメンタル更新をサポート
"""

import asyncio
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path

from .logging import get_logger


logger = get_logger(__name__)


class ChangeType(Enum):
    """Git変更タイプ"""
    ADDED = auto()
    MODIFIED = auto()
    DELETED = auto()
    RENAMED = auto()
    COPIED = auto()
    UNTRACKED = auto()


@dataclass
class GitChange:
    """Git変更情報"""
    path: Path
    change_type: ChangeType
    old_path: Path | None = None  # For renames
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        if self.change_type == ChangeType.RENAMED and self.old_path:
            return f"{self.change_type.name}: {self.old_path} -> {self.path}"
        return f"{self.change_type.name}: {self.path}"


class GitOperations:
    """
    Git操作ユーティリティクラス

    REQ-STR-004: Git連携による差分検出
    - 変更ファイルの検出
    - コミット履歴の取得
    - ファイル内容の取得（特定リビジョン）
    """

    def __init__(self, repo_path: Path):
        """
        Args:
            repo_path: Gitリポジトリのルートパス
        """
        self.repo_path = repo_path.resolve()
        self._validate_repo()

    def _validate_repo(self) -> None:
        """リポジトリの妥当性を検証"""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")

    async def get_changed_files(
        self,
        since: str | None = None,
        include_untracked: bool = True,
    ) -> list[GitChange]:
        """
        変更されたファイルを取得

        Args:
            since: 比較対象（コミットハッシュ、ブランチ名など）
            include_untracked: 未追跡ファイルを含めるか

        Returns:
            変更ファイルのリスト
        """
        changes: list[GitChange] = []

        # Staged and unstaged changes
        if since:
            cmd = ["git", "diff", "--name-status", since]
        else:
            cmd = ["git", "diff", "--name-status", "HEAD"]

        try:
            result = await self._run_git_command(cmd)
            changes.extend(self._parse_diff_output(result))
        except subprocess.CalledProcessError:
            # No commits yet or other error
            pass

        # Staged changes
        try:
            staged_cmd = ["git", "diff", "--name-status", "--cached"]
            result = await self._run_git_command(staged_cmd)
            changes.extend(self._parse_diff_output(result))
        except subprocess.CalledProcessError:
            pass

        # Untracked files
        if include_untracked:
            try:
                untracked_cmd = [
                    "git", "ls-files", "--others", "--exclude-standard"
                ]
                result = await self._run_git_command(untracked_cmd)
                for line in result.strip().split("\n"):
                    if line:
                        changes.append(GitChange(
                            path=Path(line),
                            change_type=ChangeType.UNTRACKED,
                        ))
            except subprocess.CalledProcessError:
                pass

        return self._deduplicate_changes(changes)

    def _parse_diff_output(self, output: str) -> list[GitChange]:
        """git diff --name-status の出力をパース"""
        changes = []
        for line in output.strip().split("\n"):
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 2:
                continue

            status = parts[0]
            path = Path(parts[1])

            if status.startswith("R"):
                # Rename: R100\told_path\tnew_path
                old_path = path
                new_path = Path(parts[2]) if len(parts) > 2 else path
                changes.append(GitChange(
                    path=new_path,
                    change_type=ChangeType.RENAMED,
                    old_path=old_path,
                ))
            elif status.startswith("C"):
                # Copy
                changes.append(GitChange(
                    path=Path(parts[2]) if len(parts) > 2 else path,
                    change_type=ChangeType.COPIED,
                    old_path=path,
                ))
            elif status == "A":
                changes.append(GitChange(
                    path=path,
                    change_type=ChangeType.ADDED,
                ))
            elif status == "D":
                changes.append(GitChange(
                    path=path,
                    change_type=ChangeType.DELETED,
                ))
            elif status == "M":
                changes.append(GitChange(
                    path=path,
                    change_type=ChangeType.MODIFIED,
                ))

        return changes

    def _deduplicate_changes(
        self, changes: list[GitChange]
    ) -> list[GitChange]:
        """重複する変更を除去"""
        seen = set()
        result = []
        for change in changes:
            key = (str(change.path), change.change_type)
            if key not in seen:
                seen.add(key)
                result.append(change)
        return result

    async def get_file_content(
        self,
        path: Path,
        revision: str = "HEAD",
    ) -> str | None:
        """
        特定リビジョンのファイル内容を取得

        Args:
            path: ファイルパス（リポジトリルートからの相対パス）
            revision: Gitリビジョン（コミットハッシュ、ブランチ名など）

        Returns:
            ファイル内容、取得できない場合はNone
        """
        cmd = ["git", "show", f"{revision}:{path}"]
        try:
            return await self._run_git_command(cmd)
        except subprocess.CalledProcessError:
            logger.warning(f"Failed to get content: {path}@{revision}")
            return None

    async def get_current_branch(self) -> str | None:
        """現在のブランチ名を取得"""
        cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        try:
            result = await self._run_git_command(cmd)
            return result.strip()
        except subprocess.CalledProcessError:
            return None

    async def get_commit_hash(self, revision: str = "HEAD") -> str | None:
        """コミットハッシュを取得"""
        cmd = ["git", "rev-parse", revision]
        try:
            result = await self._run_git_command(cmd)
            return result.strip()
        except subprocess.CalledProcessError:
            return None

    async def get_tracked_files(
        self,
        patterns: list[str] | None = None,
    ) -> list[Path]:
        """
        追跡対象のファイル一覧を取得

        Args:
            patterns: ファイルパターン（glob形式）

        Returns:
            ファイルパスのリスト
        """
        cmd = ["git", "ls-files"]
        if patterns:
            cmd.extend(patterns)

        try:
            result = await self._run_git_command(cmd)
            return [
                Path(line)
                for line in result.strip().split("\n")
                if line
            ]
        except subprocess.CalledProcessError:
            return []

    async def _run_git_command(self, cmd: list[str]) -> str:
        """Git コマンドを非同期で実行"""
        logger.debug(f"Running git command: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.error(f"Git command failed: {error_msg}")
            raise subprocess.CalledProcessError(
                process.returncode or 1,
                cmd,
                stdout,
                stderr,
            )

        return stdout.decode()

    def get_repo_root(self) -> Path:
        """リポジトリルートを返す"""
        return self.repo_path
