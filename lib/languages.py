"""
Language configuration loader.
Loads YAML configs from lib/languages/ directory.
"""

import os
import yaml
from typing import Optional

_config_cache: dict[str, dict] = {}
_languages_dir: Optional[str] = None


def _get_languages_dir() -> str:
    global _languages_dir
    if _languages_dir is None:
        _languages_dir = os.path.join(os.path.dirname(__file__), "languages")
    return _languages_dir


def get_language_config(language: str) -> dict:
    """
    Get config for a language.

    Args:
        language: Language key (e.g., "javascript", "csharp", "cpp", "java", "python")

    Returns:
        Config dict with: name, extensions, skip_dirs, skip_patterns, prompt, default_result
    """
    key = language.lower().strip()
    aliases = {
        "js": "javascript", "ts": "javascript", "typescript": "javascript",
        "cs": "csharp", "c#": "csharp",
        "c++": "cpp", "c": "cpp",
        "py": "python",
    }
    canonical = aliases.get(key, key)

    if canonical in _config_cache:
        return _config_cache[canonical]

    yaml_path = os.path.join(_get_languages_dir(), f"{canonical}.yaml")
    if not os.path.exists(yaml_path):
        available = [f[:-5] for f in os.listdir(_get_languages_dir()) if f.endswith(".yaml")]
        raise ValueError(f"Unknown language '{language}'. Available: {', '.join(sorted(available))}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if "extensions" in config:
        config["extensions"] = set(config["extensions"])
    if "skip_dirs" in config:
        config["skip_dirs"] = set(config["skip_dirs"])

    _config_cache[canonical] = config
    return config
