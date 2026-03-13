"""
Generic file collector.
Walks a directory and collects files matching given extensions, skipping configured directories.
"""

import os
import fnmatch
from typing import Optional


def collect_files(
    root_dir: str,
    extensions: set[str],
    skip_dirs: set[str],
    skip_patterns: Optional[list[str]] = None,
) -> list[tuple[str, str]]:
    """
    Collect files from a directory tree.

    Args:
        root_dir: Root directory to walk
        extensions: Set of file extensions to include (e.g. {".js", ".ts"})
        skip_dirs: Set of directory names to skip (e.g. {"node_modules", ".git"})
        skip_patterns: Optional list of filename patterns to skip (e.g. ["*.min.js"])

    Returns:
        List of (relative_path, content) tuples
    """
    root_dir = os.path.abspath(root_dir)
    files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]

        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext not in extensions:
                continue
            if skip_patterns and _matches_pattern(filename, skip_patterns):
                continue

            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, root_dir).replace(os.sep, "/")

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                files.append((rel_path, content))
            except Exception as e:
                print(f"  Warning: Could not read {rel_path}: {e}")

    return files


def _matches_pattern(filename: str, patterns: list[str]) -> bool:
    lower = filename.lower()
    for pattern in patterns:
        if fnmatch.fnmatch(lower, pattern.lower()):
            return True
    return False
