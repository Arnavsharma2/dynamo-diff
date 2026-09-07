import * as vscode from 'vscode';
import * as assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createHash } from 'node:crypto';

const exec = promisify(execFile);

export async function run(): Promise<void> {
    const project = process.env.DYNAMO_DIFF_PROJECT!;
    const temporary = process.env.DYNAMO_DIFF_TEST_TEMP!;
    const python = process.env.DYNAMO_DIFF_PYTHON!;
    const checks: string[] = [];
    const extension = vscode.extensions.getExtension('dynamo-diff.dynamo-diff');
    assert.ok(extension, 'Dynamo Diff must be registered');
    const implementation = path.join(extension.extensionPath, extension.packageJSON.main);
    const { Runner, comparisonTable } = require(implementation) as typeof import('../../extension');
    if (process.env.DYNAMO_DIFF_EXPECT_INSTALLED) {
        assert.ok(extension.extensionPath.startsWith(path.join(temporary, 'extensions') + path.sep));
        const digest = createHash('sha256').update(await fs.readFile(implementation)).digest('hex');
        assert.equal(digest, process.env.DYNAMO_DIFF_EXPECTED_MAIN_SHA256);
        checks.push('activation from the isolated VSIX install; installed JavaScript matches the build');
    }
    const api = await extension.activate();
    checks.push('activation');

    const importCase = async (name: string) => {
        const bundle = path.join(project, 'fixtures/captures', name);
        return await vscode.commands.executeCommand<any>('dynamoDiff.importCapture', {
            reportPath: path.join(bundle, 'report'), manifestPath: path.join(bundle, 'manifest.json'),
        });
    };
    const before = await importCase('edit_before');
    const after = await importCase('edit_after');
    assert.equal(before.counts.completed, 3);
    assert.equal(after.counts.completed, 2);
    assert.equal((await importCase('edit_before')).capture_id, before.capture_id);
    checks.push('import, duplicate import, store and workspace paths containing spaces');

    const report = await vscode.commands.executeCommand<any>('dynamoDiff.compareCaptures', {
        baselineId: before.capture_id, candidateId: after.capture_id,
    });
    const config = vscode.workspace.getConfiguration('dynamoDiff');
    const cli = await exec(python, ['-m', 'dynamo_diff.cli', '--store', config.get<string>('storePath')!,
        'compare', before.capture_id, after.capture_id, '--format', 'json']);
    assert.deepEqual(report, JSON.parse(cli.stdout));
    assert.deepEqual(api.getReport(), report);
    const row = report.functions.find((item: any) => item.baseline[0]?.source.function === 'compute');
    assert.equal(row.match_status, 'matched');
    assert.equal(row.match_method, 'source_diff_function_boundary');
    assert.equal(row.baseline_counts.confirmed_successful_recompilations, 2);
    assert.equal(row.candidate_counts.confirmed_successful_recompilations, 0);
    const roots = api.getRootItems();
    assert.equal(roots.length, 1 + report.functions.length);
    assert.ok(roots.some((item: any) => item.label === 'compute' && item.description.includes('2 → 0')));
    checks.push('CLI/editor full JSON parity and native results tree');

    const initialEditorGroups = vscode.window.tabGroups.all.length;
    const sourceBefore = await vscode.commands.executeCommand<any>('dynamoDiff.openSource', {
        captureId: before.capture_id, functionId: row.baseline[0].id,
    });
    const baselineEditor = vscode.window.activeTextEditor!;
    const baselineUri = baselineEditor.document.uri.toString();
    assert.equal(baselineEditor.document.uri.scheme, 'dynamo-diff');
    assert.equal(baselineEditor.document.languageId, 'python');
    assert.equal(baselineEditor.document.getText(), sourceBefore.text);
    assert.equal(baselineEditor.selection.start.line, sourceBefore.first_line - 1);
    // Test the user's typing path. Extension API edits can change virtual buffers
    // even when normal editor typing is read-only; they never write our snapshots.
    await vscode.commands.executeCommand('default:type', { text: '# must not change captured source\n' });
    assert.equal(baselineEditor.document.getText(), sourceBefore.text);
    const sourceAfter = await vscode.commands.executeCommand<any>('dynamoDiff.openSource', {
        captureId: after.capture_id, functionId: row.candidate[0].id,
    });
    assert.notEqual(sourceBefore.sha256, sourceAfter.sha256);
    assert.notEqual(vscode.window.activeTextEditor!.document.uri.toString(), baselineUri);
    assert.equal(vscode.window.activeTextEditor!.document.getText(), sourceAfter.text);
    checks.push('separate immutable baseline/candidate source, line navigation and read-only editing');

    const evidence = await vscode.commands.executeCommand<any>('dynamoDiff.openEvidence', {
        captureId: before.capture_id, evidenceId: row.baseline[0].evidence_ids[0],
    });
    const evidenceText = vscode.window.activeTextEditor!.document.getText();
    assert.ok(evidenceText.includes(evidence.sha256));
    assert.ok(evidenceText.includes(evidence.text));
    assert.ok(evidence.text.length <= 6000);
    await vscode.commands.executeCommand('dynamoDiff.showReport');
    assert.deepEqual(JSON.parse(vscode.window.activeTextEditor!.document.getText()), report);
    checks.push('bounded evidence with artifact provenance and JSON report navigation');

    const table = await vscode.commands.executeCommand<string>('dynamoDiff.showTable');
    assert.ok(table?.includes('| Completed compilations | 3 | 2 |'));
    assert.ok(table?.includes('| Confirmed successful recompilations | 2 | 0 |'));
    assert.ok(table?.includes('not measured'));
    assert.ok(!table?.includes('undefined'));
    // The built-in Markdown command returns before its preview tab is activated.
    await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
            subscription.dispose();
            reject(new Error('Show Comparison Table did not select its rendered Markdown preview'));
        }, 5000);
        const check = () => {
            if (vscode.window.tabGroups.activeTabGroup.activeTab?.input instanceof vscode.TabInputWebview) {
                clearTimeout(timeout); subscription.dispose(); resolve();
            }
        };
        const subscription = vscode.window.tabGroups.onDidChangeTabs(check);
        check();
    });
    assert.equal(vscode.window.tabGroups.all.length, initialEditorGroups,
        'Source, evidence and table navigation must not keep splitting the workbench');
    checks.push('captured views reuse the active editor group and the table selects its rendered preview');
    const malicious = structuredClone(report);
    malicious.functions[0].candidate[0].source.relative_path = '<img src="https://example.invalid/">![remote](https://example.invalid/)\n|';
    const safeTable = comparisonTable(malicious);
    assert.ok(!safeTable.includes('<img'));
    assert.ok(!safeTable.includes('![remote]'));
    assert.ok(safeTable.includes('&lt;img'));
    checks.push('baseline/candidate Markdown table with escaped untrusted labels');

    await assert.rejects(async () => vscode.commands.executeCommand('dynamoDiff.importCapture', {
        reportPath: path.join(temporary, 'nonexistent capture'),
    }), /missing_artifact: Cannot read artifact: raw.jsonl/);
    await assert.rejects(async () => vscode.commands.executeCommand('dynamoDiff.openSource'), /Choose Open captured source/);
    assert.deepEqual(api.getReport(), report, 'Failed command must retain last valid result');
    checks.push('actionable errors and last successful report preserved');

    // Exercise the actual process runner and cancellation token, rather than a mocked promise.
    const fakeContext = { storageUri: vscode.Uri.file(path.join(temporary, 'context')), globalStorageUri: vscode.Uri.file(temporary) } as vscode.ExtensionContext;
    const runner = new Runner(fakeContext);
    const cancelled = new vscode.CancellationTokenSource();
    cancelled.cancel();
    await assert.rejects(() => runner.run(['analyze', before.capture_id], cancelled.token), vscode.CancellationError);
    cancelled.dispose();
    if (process.platform !== 'win32') {
        const realPython = (await exec(python, ['-c', 'import sys; print(sys.executable)'])).stdout.trim();
        const stub = path.join(temporary, 'sleeping interpreter');
        const marker = path.join(temporary, 'child.pid');
        // /usr/bin/env with an argument containing spaces is not portable; use the real interpreter's path.
        const resolvedPython = await fs.realpath(realPython);
        await fs.writeFile(stub, `#!${resolvedPython}\nimport os,time\nfrom pathlib import Path\nPath(${JSON.stringify(marker)}).write_text(str(os.getpid()))\ntime.sleep(120)\n`, { mode: 0o700 });
        await config.update('pythonPath', stub, vscode.ConfigurationTarget.Workspace);
        const token = new vscode.CancellationTokenSource();
        try {
            const pending = runner.run(['anything'], token.token);
            const rejected = assert.rejects(pending, vscode.CancellationError);
            const deadline = Date.now() + 10_000;
            while (true) {
                try { await fs.access(marker); break; }
                catch { if (Date.now() > deadline) { throw new Error('Cancellation test child did not start'); } }
                await new Promise(resolve => setTimeout(resolve, 30));
            }
            const pid = Number(await fs.readFile(marker, 'utf8'));
            token.cancel();
            await rejected;
            assert.throws(() => process.kill(pid, 0), /ESRCH|not found/i);
            checks.push('in-flight cancellation terminates the actual child process');
        } finally {
            token.cancel(); token.dispose();
            await config.update('pythonPath', python, vscode.ConfigurationTarget.Workspace);
        }
    }
    checks.push('pre-cancelled operation');
    const result = { vscode: vscode.version, platform: process.platform,
        installation: process.env.DYNAMO_DIFF_EXPECT_INSTALLED ? 'vsix' : 'development',
        vsix_sha256: process.env.DYNAMO_DIFF_VSIX_SHA256,
        checks, passed: checks.length };
    console.log(JSON.stringify(result, null, 2));
    if (process.env.DYNAMO_DIFF_TEST_RESULT) {
        await fs.mkdir(path.dirname(process.env.DYNAMO_DIFF_TEST_RESULT), { recursive: true });
        await fs.writeFile(process.env.DYNAMO_DIFF_TEST_RESULT, JSON.stringify(result, null, 2) + '\n');
    }
}
