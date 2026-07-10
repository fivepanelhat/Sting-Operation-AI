"""Bounded flywheel JSONL helpers for SD-card edge nodes."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("sting.flywheel")

DEFAULT_MAX_BYTES = int(os.getenv("STING_FLYWHEEL_MAX_BYTES", str(5 * 1024 * 1024)))
DEFAULT_KEEP_LINES = int(os.getenv("STING_FLYWHEEL_KEEP_LINES", "2000"))


def rotate_flywheel_if_needed(
    path: str | Path,
    max_bytes: int = DEFAULT_MAX_BYTES,
    keep_lines: int = DEFAULT_KEEP_LINES,
) -> bool:
    """
    Trim a JSONL flywheel when over max_bytes.
    Returns True if the file was modified.
    """
    p = Path(path)
    if not p.is_file():
        return False
    try:
        size = p.stat().st_size
        if size <= max_bytes:
            return False
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) > keep_lines:
            kept = lines[-keep_lines:]
            p.write_text("\n".join(kept) + "\n", encoding="utf-8")
            logger.warning("Flywheel rotated: kept last %d lines (%s)", keep_lines, p)
            return True
        # Few huge lines — keep last half of bytes
        data = p.read_bytes()
        p.write_bytes(data[-(max_bytes // 2) :])
        logger.warning("Flywheel rotated by byte trim (%s)", p)
        return True
    except OSError as e:
        logger.error("Flywheel rotation failed: %s", e)
        return False
