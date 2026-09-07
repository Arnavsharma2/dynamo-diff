"""Create a paced visual walkthrough from actual CLI subprocess output.

Optional authoring dependencies: Pillow 12.3 and an ffmpeg executable.
This produces a presentation of captured output, not a native editor recording.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H = 1280, 720
BG, PANEL, TEXT, MUTED = '#101822', '#192532', '#f0f5fa', '#a8b9ca'
GREEN, ORANGE = '#6ee7bd', '#ffbf86'
DURATIONS = [8, 12, 14, 16, 12, 10]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--python', required=True, help='Interpreter with the tested Dynamo Diff package')
    p.add_argument('--ffmpeg', required=True)
    p.add_argument('--font', required=True)
    p.add_argument('--mono-font', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise SystemExit('Choose a new output directory')
    out = args.output.resolve()
    out.mkdir(parents=True)
    steps = []
    with tempfile.TemporaryDirectory(prefix='dynamo-diff-release-demo-') as tmp:
        base = [args.python, '-m', 'dynamo_diff.cli', '--store', str(Path(tmp) / 'store')]

        def cli(*arguments):
            command = [*base, *arguments]
            start = time.monotonic()
            r = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60, check=True)
            steps.append({'argv': command, 'exit_code': r.returncode, 'stdout': r.stdout,
                          'stderr': r.stderr, 'subprocess_wall_seconds': time.monotonic() - start})
            return json.loads(r.stdout)

        ids = []
        for case in ['edit_before', 'edit_after']:
            directory = ROOT / 'fixtures/captures' / case
            ids.append(cli('import', str(directory / 'report'), '--manifest', str(directory / 'manifest.json'))['capture_id'])
        report = cli('compare', *ids, '--format', 'json')
        row = next(r for r in report['functions'] if r['match_status'] == 'matched')
        before = cli('source', ids[0], row['baseline'][0]['id'])
        after = cli('source', ids[1], row['candidate'][0]['id'])
        capture = cli('analyze', ids[0], '--format', 'json')
        # The evidence ID is discovered from the normalized capture, not guessed.
        reason = next(reason for event in capture['compilations'] for reason in event['reasons'])
        evidence = cli('evidence', ids[0], reason['evidence_id'], '--max-chars', '4000')

    assert report['baseline_counts']['completed'] == 3 and report['candidate_counts']['completed'] == 2
    assert row['baseline_counts']['completed'] == 3 and row['candidate_counts']['completed'] == 1
    assert report['performance_conclusion'] == 'not_measured'
    assert 'step == 1' in evidence['text']
    assert before['sha256'] != after['sha256']

    def font(size, mono=False):
        return ImageFont.truetype(args.mono_font if mono else args.font, size)

    def text(draw, xy, value, size=26, fill=TEXT, mono=False):
        draw.text(xy, value, font=font(size, mono), fill=fill, spacing=8)

    def frame(number, title, subtitle):
        im = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((52, 36, 192, 67), radius=8, fill=GREEN)
        text(d, (64, 40), 'DYNAMO DIFF', 17, BG)
        text(d, (1070, 40), f'{number:02d} / 06', 19, MUTED, True)
        text(d, (52, 92), title, 43)
        text(d, (54, 154), subtitle, 24, MUTED)
        d.line((52, 644, 1228, 644), fill='#334458', width=1)
        for j in range(6):
            d.rounded_rectangle((54+j*35, 675, 79+j*35, 680), radius=2, fill=GREEN if j < number else '#334458')
        text(d, (300, 662), 'Actual CLI output • paced walkthrough • no application-speed claim', 18, MUTED)
        return im, d

    def panel(d, box):
        d.rounded_rectangle(box, radius=15, fill=PANEL)

    def function(source):
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'compute')
        return '\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])

    images = []
    im, d = frame(1, 'What changed in torch.compile?', 'Compare two saved captures. Follow the original evidence.')
    panel(d, (54, 224, 1226, 549))
    text(d, (86, 250), 'A small source edit. Different compiler behavior.', 32)
    text(d, (86, 321), 'BASELINE', 20, ORANGE)
    text(d, (703, 321), 'CANDIDATE', 20, GREEN)
    text(d, (86, 357), '3 completed compilations', 36)
    text(d, (703, 357), '2 completed compilations', 36)
    text(d, (585, 360), '→', 42, GREEN)
    text(d, (86, 435), 'Which function changed? Which guard failed?', 30, MUTED)
    text(d, (54, 580), 'One Python core → CLI / local MCP / VS Code', 27, GREEN)
    images.append(im)

    im, d = frame(2, 'The edit removes a scalar branch', 'The output expression is unchanged in this authored workload.')
    for left, label, source, accent in [(54, 'BASELINE · model.py:9', before['text'], ORANGE),
                                         (651, 'CANDIDATE · model.py:9', after['text'], GREEN)]:
        panel(d, (left, 222, left+574, 554))
        text(d, (left+22, 243), label, 21, accent)
        snippet = function(source)
        # Omit only the explanatory comment in the narrow side-by-side excerpt.
        snippet = '\n'.join(line for line in snippet.splitlines() if not line.lstrip().startswith('#'))
        text(d, (left+22, 300), snippet, 21, TEXT, True)
    text(d, (54, 582), 'The candidate also adds a helper, shifting the run-local frame IDs.', 25, MUTED)
    images.append(im)

    im, d = frame(3, 'Match the function across the edit', 'Selected fields from the actual comparison JSON.')
    panel(d, (54, 224, 1226, 556))
    text(d, (80, 244), 'Function', 23, MUTED)
    text(d, (480, 244), 'Completed', 23, MUTED)
    text(d, (795, 244), 'Confirmed recompiles', 23, MUTED)
    d.line((80, 288, 1200, 288), fill='#334458')
    for y, name, completed, recompiles in [(319, 'compute · matched', '3 → 1', '2 → 0'),
                                           (398, 'helper · unmatched', '0 → 1', '0 → 0'),
                                           (484, 'Capture totals', '3 → 2', '2 → 0')]:
        text(d, (80, y), name, 27)
        text(d, (480, y), completed, 31, GREEN, True)
        text(d, (795, y), recompiles, 31, GREEN, True)
    text(d, (54, 584), 'Source-diff matching preserves the new helper in candidate totals.', 25, MUTED)
    images.append(im)

    im, d = frame(4, 'Open the original guard reason', 'The scalar guard is recorded on the baseline; inspect its provenance.')
    panel(d, (54, 224, 1226, 566))
    text(d, (80, 246), 'BASELINE EVIDENCE', 21, ORANGE)
    text(d, (80, 291), '0/0: step == 1', 36, TEXT, True)
    text(d, (80, 355), 'Captured source: if step > 0', 25, MUTED, True)
    text(d, (80, 411), f"Artifact: {evidence['artifact']}", 23, TEXT, True)
    text(d, (80, 454), f"Record: {evidence['record_line']}", 23, TEXT, True)
    text(d, (80, 499), 'SHA-256: '+evidence['sha256'][:28]+'…', 23, MUTED, True)
    text(d, (54, 588), 'Full original text and hash are retained in the accompanying receipt.', 24, MUTED)
    images.append(im)

    im, d = frame(5, 'Keep the conclusions separate', 'Fewer compilations alone do not establish a faster application.')
    for y, label, value, note in [(232, 'SOURCE MATCH', 'matched', 'Unique function boundary across the edit'),
                                (350, 'WORKLOAD', report['workload_comparability'], 'Matching declarations; not runtime-equivalence proof'),
                                (468, 'APPLICATION SPEED', 'not measured', 'No timing or optimization claim')]:
        panel(d, (54, y, 1226, y+103))
        text(d, (78, y+17), label, 18, MUTED)
        text(d, (365, y+10), value, 29, GREEN)
        text(d, (365, y+55), note, 23, MUTED)
    images.append(im)

    im, d = frame(6, 'Try the recorded example', 'Inspect saved captures without installing PyTorch or using a GPU.')
    panel(d, (54, 224, 1226, 550))
    text(d, (80, 249), 'github.com/Arnavsharma2/dynamo-diff', 36, GREEN)
    text(d, (80, 316), 'CLI', 23, MUTED)
    text(d, (270, 310), 'python tools/demo.py', 27, TEXT, True)
    text(d, (80, 377), 'VS CODE', 23, MUTED)
    text(d, (270, 373), 'Import Capture → Compare Captures', 27)
    text(d, (80, 439), 'AGENTS', 23, MUTED)
    text(d, (270, 435), 'Local MCP tools; experimental integration', 27)
    text(d, (54, 584), 'The recorded agent pilot showed no end-to-end improvement.', 25, MUTED)
    images.append(im)

    for i, im in enumerate(images, 1):
        im.save(out / f'chapter-{i:02}.png')
    images[2].save(out / 'poster.png')
    images[0].save(out / 'walkthrough.gif', save_all=True, append_images=images[1:],
                   duration=[n*1000 for n in DURATIONS], loop=0, optimize=True)
    concat = out / 'timeline.ffconcat'
    concat.write_text('ffconcat version 1.0\n'+''.join(f"file 'chapter-{i+1:02}.png'\nduration {seconds}\n"
                    for i, seconds in enumerate(DURATIONS))+"file 'chapter-06.png'\n")
    subprocess.run([args.ffmpeg, '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', str(concat), '-vf', 'fps=12,format=yuv420p', '-t', str(sum(DURATIONS)),
                    '-c:v', 'libx264', '-crf', '22', '-movflags', '+faststart', str(out/'walkthrough.mp4')], check=True)
    public_receipt = {'created_at': datetime.now(timezone.utc).isoformat(),
        'kind': 'Paced presentation of actual CLI subprocess output; not a native editor screen recording or a benchmark',
        'duration_seconds': sum(DURATIONS), 'chapter_seconds': DURATIONS,
        'script_sha256': sha(Path(__file__).read_bytes()), 'steps': steps,
        'capture_ids': ids, 'source_before_sha256': before['sha256'], 'source_after_sha256': after['sha256'],
        'evidence_sha256': evidence['sha256'],
        'media': {name: sha((out/name).read_bytes()) for name in ['walkthrough.mp4','walkthrough.gif','poster.png']}}
    (out/'receipt.json').write_text(json.dumps(public_receipt, indent=2)+'\n')
    (out/'TRANSCRIPT.md').write_text('''# Dynamo Diff release walkthrough

This 72-second presentation uses actual CLI output from the retained authored captures. It is paced for reading, not a native editor recording or a runtime benchmark. `receipt.json` retains commands, original stdout, exit codes and hashes.

1. **0–8 seconds:** the baseline has three completed compilations; the candidate has two.
2. **8–20 seconds:** the candidate removes a redundant scalar branch and adds a helper. The source excerpts omit only the explanatory comment.
3. **20–34 seconds:** `compute` matches across changed source hashes/frame IDs, moving from three to one completed compilations and two to zero confirmed recompiles. The unmatched helper remains in totals.
4. **34–50 seconds:** baseline evidence contains `step == 1`, the original `if step > 0` context, artifact path, record number and SHA-256. The displayed hash is shortened; the complete value is in the receipt.
5. **50–62 seconds:** source correspondence, workload declarations and application performance are separate. Manifest consistency is not runtime-equivalence proof; application speed is not measured.
6. **62–72 seconds:** use the recorded CLI example or the VS Code import/compare flow. The local MCP interface is experimental; the existing pilot found no end-to-end agent improvement.
''')
    print(json.dumps({'output': str(out), 'commands_passed': len(steps), 'duration_seconds': sum(DURATIONS)}))


if __name__ == '__main__':
    main()
