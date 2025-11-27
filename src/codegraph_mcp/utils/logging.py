"""
Logging Utilities
=================

構造化ロギングとログ設定を提供します。
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# グローバルなログフォーマット設定
DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
DEBUG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
)

# ログレベルのマッピング
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class ColoredFormatter(logging.Formatter):
    """
    ターミナル出力用のカラーフォーマッター
    """

    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        use_colors: bool = True,
    ):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors:
            color = self.COLORS.get(record.levelno, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"

        return super().format(record)


class StructuredLogger(logging.Logger):
    """
    構造化ロギングをサポートするカスタムロガー
    """

    def structured(
        self,
        level: int,
        msg: str,
        **kwargs: Any,
    ) -> None:
        """
        構造化データ付きでログ出力

        Args:
            level: ログレベル
            msg: メッセージ
            **kwargs: 構造化データ
        """
        if kwargs:
            extra_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            msg = f"{msg} | {extra_str}"
        self.log(level, msg)

    def info_struct(self, msg: str, **kwargs: Any) -> None:
        self.structured(logging.INFO, msg, **kwargs)

    def debug_struct(self, msg: str, **kwargs: Any) -> None:
        self.structured(logging.DEBUG, msg, **kwargs)

    def warning_struct(self, msg: str, **kwargs: Any) -> None:
        self.structured(logging.WARNING, msg, **kwargs)

    def error_struct(self, msg: str, **kwargs: Any) -> None:
        self.structured(logging.ERROR, msg, **kwargs)


# カスタムロガークラスを登録
logging.setLoggerClass(StructuredLogger)


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    use_colors: bool = True,
    debug_mode: bool = False,
) -> None:
    """
    ロギングをセットアップ

    Args:
        level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: ログファイルパス（指定時はファイルにも出力）
        use_colors: ターミナル出力に色を使用するか
        debug_mode: デバッグモード（より詳細なフォーマット）
    """
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    log_format = DEBUG_FORMAT if debug_mode else DEFAULT_FORMAT

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 既存のハンドラーをクリア
    root_logger.handlers.clear()

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_formatter = ColoredFormatter(log_format, use_colors=use_colors)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ファイルハンドラー（オプション）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # codegraph_mcp 名前空間のロガー設定
    pkg_logger = logging.getLogger("codegraph_mcp")
    pkg_logger.setLevel(log_level)


def get_logger(name: str) -> StructuredLogger:
    """
    指定した名前のロガーを取得

    Args:
        name: ロガー名（通常は __name__）

    Returns:
        構造化ロギング対応のロガーインスタンス
    """
    return logging.getLogger(name)  # type: ignore


class LogContext:
    """
    ログコンテキストマネージャー

    処理の開始・終了を自動でログ出力します。

    Usage:
        with LogContext(logger, "Processing file"):
            process_file()
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        level: int = logging.INFO,
        **context,
    ):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.context = context
        self.start_time: datetime | None = None

    def __enter__(self) -> "LogContext":
        self.start_time = datetime.now()
        context_str = " | ".join(
            f"{k}={v}" for k, v in self.context.items()
        ) if self.context else ""

        msg = f"Starting: {self.operation}"
        if context_str:
            msg = f"{msg} | {context_str}"

        self.logger.log(self.level, msg)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        elapsed = datetime.now() - self.start_time if self.start_time else None
        elapsed_ms = elapsed.total_seconds() * 1000 if elapsed else 0

        if exc_type is not None:
            self.logger.error(
                f"Failed: {self.operation} | "
                f"error={exc_type.__name__}: {exc_val} | "
                f"elapsed_ms={elapsed_ms:.2f}"
            )
        else:
            self.logger.log(
                self.level,
                f"Completed: {self.operation} | elapsed_ms={elapsed_ms:.2f}"
            )


class PerformanceLogger:
    """
    パフォーマンス計測用ロガー

    Usage:
        perf = PerformanceLogger(logger)
        perf.mark("start")
        # ... processing ...
        perf.mark("after_parse")
        # ... more processing ...
        perf.mark("end")
        perf.report()
    """

    def __init__(self, logger: logging.Logger, operation: str = ""):
        self.logger = logger
        self.operation = operation
        self.marks: list[tuple[str, datetime]] = []

    def mark(self, name: str) -> None:
        """マークポイントを記録"""
        self.marks.append((name, datetime.now()))

    def report(self, level: int = logging.DEBUG) -> None:
        """計測結果をログ出力"""
        if len(self.marks) < 2:
            return

        parts = []
        for i in range(1, len(self.marks)):
            prev_name, prev_time = self.marks[i - 1]
            curr_name, curr_time = self.marks[i]
            elapsed_ms = (curr_time - prev_time).total_seconds() * 1000
            parts.append(f"{prev_name}->{curr_name}: {elapsed_ms:.2f}ms")

        total_ms = (
            self.marks[-1][1] - self.marks[0][1]
        ).total_seconds() * 1000

        msg = f"Performance[{self.operation}] | " + " | ".join(parts)
        msg += f" | total: {total_ms:.2f}ms"

        self.logger.log(level, msg)
