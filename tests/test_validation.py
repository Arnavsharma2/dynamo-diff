import json
from pathlib import Path
import shutil

import pytest

from dynamo_diff.adapters.tlparse import analyze_report
from dynamo_diff.compare import comparability
from dynamo_diff.errors import DynamoDiffError

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/captures/stable"


@pytest.mark.parametrize("manifest", [{"source": []}, {"producer": "invalid"}, {"capture": {"raw_traces": {}}}, {"source": {"files": 1}}])
def test_invalid_manifest_structure_is_a_structured_error(manifest):
    with pytest.raises(DynamoDiffError) as error:
        analyze_report(FIXTURE / "report", manifest=manifest, manifest_root=FIXTURE)
    assert error.value.code == "malformed_manifest"


def test_observed_configuration_differences_override_equal_manifests(tmp_path):
    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    baseline = analyze_report(FIXTURE / "report", manifest=manifest, manifest_root=FIXTURE)
    report = tmp_path / "report"
    shutil.copytree(FIXTURE / "report", report)
    path = report / "raw.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    for record in records:
        if "compilation_metrics" in record:
            config = json.loads(record["compilation_metrics"]["dynamo_config"])
            config["recompile_limit"] = 2
            record["compilation_metrics"]["dynamo_config"] = json.dumps(config)
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
    candidate = analyze_report(report, manifest=manifest, manifest_root=FIXTURE)
    status, differences = comparability(baseline, candidate)
    assert status == "confounded"
    assert any(d["field"] == "observed.dynamo_config" for d in differences)
