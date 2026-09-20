"""
Repository relationship analyzer.

Detects relationships between files by inspecting imports.

Currently supports:
- Python imports
- Python relative imports
- JavaScript imports
- TypeScript imports
- React-style relative imports
"""

from __future__ import annotations

import posixpath
import re
from pathlib import PurePosixPath
from typing import Any


SUPPORTED_EXTENSIONS = [
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
]


def normalize_path(path: str) -> str:
    """Normalize a repository path."""

    path = path.replace("\\", "/")
    path = posixpath.normpath(path)

    if path.startswith("./"):
        path = path[2:]

    return path


def build_file_index(files: list[dict[str, Any]]) -> set[str]:
    """Create a set of repository file paths."""

    return {
        normalize_path(file["path"])
        for file in files
        if file.get("path")
    }


def find_python_imports(content: str) -> list[str]:
    """Extract Python import targets."""

    imports: list[str] = []

    # import foo
    # import foo.bar
    for match in re.finditer(
        r"^\s*import\s+([a-zA-Z_][\w.]*)",
        content,
        re.MULTILINE,
    ):
        imports.append(match.group(1))

    # from foo.bar import something
    for match in re.finditer(
        r"^\s*from\s+([a-zA-Z_][\w.]*)\s+import\s+",
        content,
        re.MULTILINE,
    ):
        imports.append(match.group(1))

    # from .foo import bar
    # from ..foo import bar
    for match in re.finditer(
        r"^\s*from\s+(\.+[a-zA-Z_][\w.]*)\s+import\s+",
        content,
        re.MULTILINE,
    ):
        imports.append(match.group(1))

    return imports


def find_javascript_imports(content: str) -> list[str]:
    """Extract JavaScript / TypeScript import targets."""

    imports: list[str] = []

    patterns = [
        r'import\s+(?:[\s\S]*?\s+from\s+)?["\']([^"\']+)["\']',
        r'require\(\s*["\']([^"\']+)["\']\s*\)',
        r'import\(\s*["\']([^"\']+)["\']\s*\)',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, content):
            imports.append(match.group(1))

    return imports


def resolve_python_import(
    source_path: str,
    import_name: str,
    file_index: set[str],
) -> str | None:
    """Resolve a Python import to a repository file."""

    source = PurePosixPath(source_path)

    # Relative import
    if import_name.startswith("."):
        dots = len(import_name) - len(import_name.lstrip("."))

        remainder = import_name[dots:]

        base = source.parent

        for _ in range(max(dots - 1, 0)):
            base = base.parent

        if remainder:
            module_parts = remainder.split(".")
            candidate_base = base.joinpath(*module_parts)
        else:
            candidate_base = base

    else:
        candidate_base = PurePosixPath(
            *import_name.split(".")
        )

    candidate = normalize_path(str(candidate_base))

    candidates = [
        candidate + ".py",
        candidate + "/__init__.py",
    ]

    for possible in candidates:
        if possible in file_index:
            return possible

    return None


def resolve_javascript_import(
    source_path: str,
    import_name: str,
    file_index: set[str],
) -> str | None:
    """Resolve a JS/TS relative import."""

    if not import_name.startswith("."):
        return None

    source_parent = PurePosixPath(source_path).parent

    candidate = normalize_path(
        str(
            source_parent.joinpath(import_name)
        )
    )

    candidates = [
        candidate,
        candidate + ".js",
        candidate + ".jsx",
        candidate + ".ts",
        candidate + ".tsx",
        candidate + ".mjs",
        candidate + ".cjs",
        candidate + "/index.js",
        candidate + "/index.jsx",
        candidate + "/index.ts",
        candidate + "/index.tsx",
    ]

    for possible in candidates:
        if possible in file_index:
            return possible

    return None


def detect_relationships(
    source_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Detect relationships between repository files.

    Each relationship looks like:

    {
        "source": "backend/apps/users/views.py",
        "target": "backend/apps/users/models.py",
        "type": "imports",
        "import": "backend.apps.users.models"
    }
    """

    file_index = build_file_index(source_files)

    relationships: list[dict[str, Any]] = []

    for file in source_files:
        source_path = normalize_path(
            file.get("path", "")
        )

        content = file.get("content", "")

        if not source_path or not content:
            continue

        extension = PurePosixPath(
            source_path
        ).suffix.lower()

        imports: list[str] = []

        if extension == ".py":
            imports = find_python_imports(content)

        elif extension in {
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".mjs",
            ".cjs",
        }:
            imports = find_javascript_imports(content)

        for import_name in imports:

            target = None

            if extension == ".py":
                target = resolve_python_import(
                    source_path,
                    import_name,
                    file_index,
                )

            elif extension in {
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".mjs",
                ".cjs",
            }:
                target = resolve_javascript_import(
                    source_path,
                    import_name,
                    file_index,
                )

            if not target:
                continue

            if target == source_path:
                continue

            relationships.append(
                {
                    "source": source_path,
                    "target": target,
                    "type": "imports",
                    "import": import_name,
                }
            )

    # Remove duplicates while preserving order.
    seen = set()
    unique_relationships = []

    for relationship in relationships:
        key = (
            relationship["source"],
            relationship["target"],
            relationship["type"],
        )

        if key in seen:
            continue

        seen.add(key)
        unique_relationships.append(
            relationship
        )

    return unique_relationships


def build_relationship_summary(
    relationships: list[dict[str, Any]],
) -> list[str]:
    """Create human-readable relationship summaries."""

    summary = []

    for relationship in relationships:
        summary.append(
            f'{relationship["source"]} imports '
            f'{relationship["target"]}'
        )

    return summary