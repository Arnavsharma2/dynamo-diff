"""Bounded file IO. Paths and trace strings are data, never commands."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import stat
from typing import Iterator

from .errors import DynamoDiffError
from .model import Limits


def json_value(text: str | bytes) -> object:
    """Reject ambiguous/non-JSON numbers, duplicate keys and excessive nesting."""
    def invalid_constant(value: str) -> None:
        raise ValueError(f"Non-finite JSON constant: {value}")

    def object_pairs(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON object key")
            result[key] = value
        return result

    value = json.loads(text, parse_constant=invalid_constant, object_pairs_hook=object_pairs)
    stack = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > 64:
            raise ValueError("JSON nesting exceeds 64 levels")
        if isinstance(item, dict):
            stack.extend((key, depth + 1) for key in item)
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
        elif isinstance(item, float) and not math.isfinite(item):
            raise ValueError("JSON number is not finite")
        elif isinstance(item, str):
            item.encode("utf-8")  # Reject unpaired surrogate escapes before serialization.
    return value


def within(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise DynamoDiffError("unsafe_path", "Artifact path must be a nonempty string without NUL bytes")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise DynamoDiffError("unsafe_path", f"Artifact path must stay inside its bundle: {relative}")
    try:
        resolved = (root / path).resolve()
    except (OSError, RuntimeError) as error:
        raise DynamoDiffError("unsafe_path", "Artifact path cannot be resolved safely") from error
    if not resolved.is_relative_to(root.resolve()):
        raise DynamoDiffError("unsafe_path", f"Artifact resolves outside its bundle: {relative}")
    return resolved


def hash_file(path: Path, max_bytes: int) -> str:
    digest = hashlib.sha256()
    total = 0
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            raise DynamoDiffError("missing_artifact", f"Artifact must be a regular file: {path.name}")
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                total += len(chunk)
                if total > max_bytes:
                    raise DynamoDiffError("resource_limit", f"File exceeds {max_bytes} bytes: {path.name}")
                digest.update(chunk)
    except OSError as error:
        raise DynamoDiffError("missing_artifact", f"Cannot read artifact: {path.name}") from error
    return digest.hexdigest()


def read_text(path: Path, max_bytes: int) -> str:
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            raise DynamoDiffError("missing_artifact", f"Artifact must be a regular file: {path.name}")
        with path.open("rb") as file:
            raw = file.read(max_bytes + 1)
    except OSError as error:
        raise DynamoDiffError("missing_artifact", f"Cannot read artifact: {path.name}") from error
    if len(raw) > max_bytes:
        raise DynamoDiffError("resource_limit", f"Artifact exceeds {max_bytes} bytes: {path.name}")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise DynamoDiffError("malformed_input", f"Artifact is not UTF-8: {path.name}") from error


def records(path: Path, limits: Limits) -> Iterator[tuple[int, int, int, dict | None]]:
    """Yield location and parsed object; malformed lines yield None, with evidence."""
    total = 0
    number = 0
    try:
        with path.open("rb") as file:
            while True:
                offset = file.tell()
                line = file.readline(limits.record_bytes + 1)
                if not line:
                    return
                number += 1
                total += len(line)
                if number > limits.records or total > limits.input_bytes or len(line) > limits.record_bytes:
                    raise DynamoDiffError("resource_limit", f"Metadata limit exceeded at record {number}")
                try:
                    value = json_value(line)
                    if not isinstance(value, dict):
                        value = None
                except (UnicodeError, ValueError, RecursionError):
                    value = None
                yield number, offset, len(line), value
    except OSError as error:
        raise DynamoDiffError("missing_artifact", "Report must contain a readable raw.jsonl") from error
