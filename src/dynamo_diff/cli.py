"""CLI entry point; structured failures have stable codes and nonzero status."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from . import __version__
from .adapters.tlparse import analyze_report
from .compare import Comparison, compare_runs
from .errors import DynamoDiffError
from .io import read_text
from .model import Capture
from .render import capture_summary, render_capture, render_comparison
from .store import Store


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="dynamo-diff", description="Compare recorded PyTorch Dynamo compilation behavior with evidence.")
    result.add_argument("--version", action="version", version=f"dynamo-diff {__version__}")
    result.add_argument("--store", type=Path, default=Path(os.environ.get("DYNAMO_DIFF_STORE", ".dynamo-diff")))
    sub = result.add_subparsers(dest="command", required=True)
    import_command = sub.add_parser("import", help="Import an existing tlparse report; does not execute a workload")
    import_command.add_argument("report", type=Path)
    import_command.add_argument("--manifest", type=Path)
    analyze = sub.add_parser("analyze", help="Describe an imported capture")
    analyze.add_argument("capture_id")
    analyze.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    compare = sub.add_parser("compare", help="Compare two imported captures")
    compare.add_argument("baseline_id")
    compare.add_argument("candidate_id")
    compare.add_argument("--source-map", type=Path, help="JSON object mapping baseline function IDs to candidate IDs")
    compare.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    evidence = sub.add_parser("evidence", help="Retrieve bounded original trace evidence")
    evidence.add_argument("capture_id")
    evidence.add_argument("evidence_id")
    evidence.add_argument("--offset", type=int, default=0)
    evidence.add_argument("--max-chars", type=int, default=6000)
    source = sub.add_parser("source", help="Read the verified source snapshot for a captured function")
    source.add_argument("capture_id")
    source.add_argument("function_id")
    schema = sub.add_parser("schema", help="Print a versioned public JSON schema")
    schema.add_argument("--kind", choices=["capture", "comparison"], default="capture")
    schema.add_argument("--output", type=Path)
    serve = sub.add_parser("serve-mcp", help="Serve local analysis tools using MCP over stdio")
    serve.add_argument("--allow-root", type=Path, action="append", required=True,
                       help="Explicit local directory the agent may import reports from; repeatable")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    store = Store(args.store)
    try:
        if args.command == "import":
            output = capture_summary(store.import_trace(args.report, manifest_path=args.manifest))
        elif args.command == "analyze":
            capture = store.load(args.capture_id)
            if args.format != "json":
                print(render_capture(capture, markdown=args.format == "markdown"), end="")
                return 0
            output = capture.model_dump(exclude={"manifest", "evidence"})
        elif args.command == "compare":
            source_map = json.loads(read_text(args.source_map, store.limits.record_bytes)) if args.source_map else None
            comparison = compare_runs(store, args.baseline_id, args.candidate_id, source_map=source_map)
            if args.format != "json":
                print(render_comparison(comparison, markdown=args.format == "markdown"), end="")
                return 0
            output = comparison.model_dump()
        elif args.command == "evidence":
            output = store.get_evidence(args.capture_id, args.evidence_id, offset=args.offset, max_chars=args.max_chars)
        elif args.command == "source":
            output = store.get_source(args.capture_id, args.function_id)
        elif args.command == "schema":
            output = (Capture if args.kind == "capture" else Comparison).model_json_schema()
            if args.output:
                args.output.write_text(json.dumps(output, indent=2) + "\n")
                return 0
        elif args.command == "serve-mcp":
            from .mcp_server import serve
            serve(store, args.allow_root)
            return 0
        else:
            raise AssertionError(args.command)
        print(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except DynamoDiffError as error:
        print(json.dumps(error.as_dict()), file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": {"code": "invalid_input", "message": str(error)}}), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print(json.dumps({"error": {"code": "cancelled", "message": "Operation cancelled"}}), file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
