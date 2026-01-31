"""
Logging configuration with Windows Unicode support
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

from app.config import settings


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure logging with proper Unicode support for Windows
    """
    # Create console with UTF-8 encoding forced
    console = Console(force_terminal=True, color_system="auto")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create Rich handler (handles Unicode properly)
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    rich_handler.setLevel(logging.INFO)
    
    # ASCII-only formatter for fallback
    ascii_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler with UTF-8 encoding
    log_file = settings.log_file_path
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(
        log_file,
        encoding='utf-8',
        mode='a'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(ascii_formatter)
    
    # Add handlers
    root_logger.addHandler(rich_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
    logging.getLogger("fastembed").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


# Safe emoji replacement for Windows compatibility
class SafeLogger:
    """Logger wrapper that converts emojis to ASCII for Windows"""
    
    EMOJI_MAP = {
        '✅': '[OK]',
        '❌': '[FAIL]',
        '⚠️': '[WARN]',
        '📊': '[STATS]',
        '📦': '[PKG]',
        '📝': '[TEXT]',
        '🖼️': '[IMG]',
        '🔬': '[ANALYZE]',
        '🏷️': '[TAG]',
        '🔑': '[KEY]',
        '🎯': '[TARGET]',
        '🔍': '[SEARCH]',
        '💾': '[SAVE]',
        '🚀': '[START]',
        '⏱️': '[TIME]',
        '📁': '[FILE]',
        '🔄': '[SYNC]',
        '✨': '[NEW]',
        '🛠️': '[TOOL]',
        '📌': '[PIN]',
        '🎵': '[AUDIO]',
        '🔊': '[SOUND]',
    }
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _sanitize(self, msg: str) -> str:
        """Replace emojis with ASCII equivalents"""
        for emoji, replacement in self.EMOJI_MAP.items():
            msg = msg.replace(emoji, replacement)
        return msg
    
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(self._sanitize(str(msg)), *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(self._sanitize(str(msg)), *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(self._sanitize(str(msg)), *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self.logger.error(self._sanitize(str(msg)), *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(self._sanitize(str(msg)), *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        self.logger.exception(self._sanitize(str(msg)), *args, **kwargs)


def get_safe_logger(name: str) -> SafeLogger:
    """Get a Windows-safe logger that converts emojis to ASCII"""
    return SafeLogger(name)