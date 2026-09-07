"""Structural checks for declarations; missing optional metadata remains inspectable."""

import re

from .errors import DynamoDiffError

SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate_manifest(manifest: dict | None) -> None:
    if manifest is None:
        return

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise DynamoDiffError("malformed_manifest", message)

    require(isinstance(manifest, dict), "Manifest must be an object")
    for section in ("source", "capture", "workload", "producer"):
        require(section not in manifest or isinstance(manifest[section], dict), f"{section} must be an object")
    for section, field, path_fields in [("source", "files", ("captured_path", "relative_path", "snapshot")),
                                        ("capture", "raw_traces", ("path",))]:
        entries = manifest.get(section, {}).get(field, [])
        require(isinstance(entries, list), f"{section}.{field} must be a list")
        for entry in entries:
            require(isinstance(entry, dict), f"{section}.{field} entries must be objects")
            for key in path_fields:
                require(isinstance(entry.get(key), str) and bool(entry[key]) and "\x00" not in entry[key],
                        f"{section}.{field}.{key} must be a nonempty path string")
            require(isinstance(entry.get("sha256"), str) and SHA256.fullmatch(entry["sha256"]) is not None,
                    f"{section}.{field}.sha256 must be a SHA-256 hex digest")
    declaration = manifest.get("capture", {})
    if declaration.get("workload_completed") is not None:
        require(type(declaration["workload_completed"]) is bool, "capture.workload_completed must be a boolean or null")
    for key in ("process_exit_code", "converter_exit_code"):
        if declaration.get(key) is not None:
            require(type(declaration[key]) is int, f"capture.{key} must be an integer or null")
    for key in ("report_sha256", "result_sha256"):
        if declaration.get(key) is not None:
            require(isinstance(declaration[key], str) and SHA256.fullmatch(declaration[key]) is not None,
                    f"capture.{key} must be a SHA-256 hex digest or null")
    for key in ("torch", "torch_git", "python", "tlparse"):
        value = manifest.get("producer", {}).get(key)
        require(value is None or isinstance(value, str), f"producer.{key} must be a string or null")
