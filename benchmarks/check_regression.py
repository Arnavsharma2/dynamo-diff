"""Compare repeated measurements on the same host/profile; no cross-host speed claims."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    baseline, candidate = [json.loads(path.read_text()) for path in [args.baseline, args.candidate]]
    if baseline["profile"] != candidate["profile"] or baseline["platform"] != candidate["platform"]:
        raise SystemExit("Incomparable measurement profile/platform; establish a separate baseline")
    left = {row["target_bytes"]: row for row in baseline["sizes"]}
    right = {row["target_bytes"]: row for row in candidate["sizes"]}
    if left.keys() != right.keys():
        raise SystemExit("Incomparable input sizes")
    issues = []
    for size, before in left.items():
        after = right[size]
        if before["metadata_sha256"] != after["metadata_sha256"] or before["actual_bytes"] != after["actual_bytes"]:
            raise SystemExit("Input changed; measurements are not a controlled implementation comparison")
        if after["median_import_seconds"] > 2 * before["median_import_seconds"]:
            issues.append(f"{size} bytes: median import time exceeds 2x baseline")
        if after["max_peak_rss_bytes"] > 1.5 * before["max_peak_rss_bytes"]:
            issues.append(f"{size} bytes: peak RSS exceeds 1.5x baseline")
    if baseline["comparison"]["fixture_pair"] != candidate["comparison"]["fixture_pair"]:
        raise SystemExit("Comparison fixtures differ")
    limit = max(.005, 3 * baseline["comparison"]["median_seconds"])
    if candidate["comparison"]["median_seconds"] > limit:
        issues.append("Warm comparison median exceeds max(5 ms, 3x baseline)")
    if candidate["comparison"]["initial_mcp_json_chars"] > 12000:
        issues.append("Initial MCP result exceeds the public response budget")
    print(json.dumps({"status": "investigate" if issues else "within_thresholds", "issues": issues}, indent=2))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
