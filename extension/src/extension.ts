import * as vscode from 'vscode';
import { execFile } from 'node:child_process';
import * as path from 'node:path';

type Counts = Record<string, number>;
type Source = { relative_path: string | null; captured_path: string | null; function: string | null; qualified_name: string | null; first_line: number | null };
type Group = { id: string; source: Source; counts: Counts; evidence_ids: string[]; guard_categories: string[] };
type Row = { match_status: string; match_method: string; baseline: Group[]; candidate: Group[]; baseline_counts: Counts; candidate_counts: Counts };
type Comparison = { id: string; baseline_id: string; candidate_id: string; capture_validity: Record<string, { artifact_structure: string; workload_completion: string }>; workload_comparability: string; baseline_counts: Counts; candidate_counts: Counts; functions: Row[]; notices: { code: string; message: string }[]; performance_conclusion: string };
type Receipt = { capture_id: string; counts: Counts; capture_validity: Record<string, string> };
type SavedCapture = { id: string; label: string };
type SourceResult = { text: string; relative_path: string | null; first_line: number | null; sha256: string };
type EvidenceResult = { text: string; artifact: string; sha256: string; record_line: number | null; truncated: boolean; next_offset: number | null; total_chars: number };

function markdownCell(value: string): string {
    return value.replace(/[\r\n\t]/g, ' ').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/[\\`*_{}\[\]()#!|]/g, character => `\\${character}`);
}

export function comparisonTable(report: Comparison): string {
    const lines = ['# Dynamo Diff', '', `Workload comparability: **${markdownCell(report.workload_comparability)}**`, '',
        '| Capture validity | Baseline | Candidate |', '|---|---|---|',
        `| Artifact structure | ${markdownCell(report.capture_validity.baseline.artifact_structure)} | ${markdownCell(report.capture_validity.candidate.artifact_structure)} |`,
        `| Workload completion | ${markdownCell(report.capture_validity.baseline.workload_completion)} | ${markdownCell(report.capture_validity.candidate.workload_completion)} |`, '',
        '| Compiler event | Baseline | Candidate |', '|---|---:|---:|'];
    for (const [key, label] of [['completed', 'Completed compilations'], ['confirmed_successful_recompilations', 'Confirmed successful recompilations'],
        ['failed', 'Failed compilations'], ['no_graph_observed', 'No graph observed'], ['unknown_outcomes', 'Unknown outcomes'],
        ['compiler_limit_events', 'Compiler limit reports'], ['fallback_reports', 'Explicit fallback reports']]) {
        lines.push(`| ${label} | ${report.baseline_counts[key]} | ${report.candidate_counts[key]} |`);
    }
    lines.push('', '| Function | Source match | Completed B → C | Confirmed recompiles B → C | Baseline guards | Candidate guards |',
        '|---|---|---:|---:|---|---|');
    for (const row of report.functions) {
        const source = (row.candidate[0] ?? row.baseline[0]).source;
        const name = `${source.relative_path ?? source.captured_path ?? '?'}:${source.qualified_name ?? source.function ?? '?'}`;
        const guards = (groups: Group[]) => markdownCell([...new Set(groups.flatMap(group => group.guard_categories))].join(', ') || 'none recorded');
        lines.push(`| ${markdownCell(name)} | ${markdownCell(row.match_status)} (${markdownCell(row.match_method)}) | ${row.baseline_counts.completed} → ${row.candidate_counts.completed} | ${row.baseline_counts.confirmed_successful_recompilations} → ${row.candidate_counts.confirmed_successful_recompilations} | ${guards(row.baseline)} | ${guards(row.candidate)} |`);
    }
    lines.push('', 'B = baseline; C = candidate. Open source and evidence from the Dynamo Diff results tree.', '',
        'Application performance: **not measured**. Source correspondence does not establish semantic equivalence.', '');
    for (const notice of report.notices) { lines.push(`- ${markdownCell(notice.message)}`); }
    return lines.join('\n') + '\n';
}

export class Runner {
    constructor(private readonly context: vscode.ExtensionContext) {}

    async run<T>(args: string[], token?: vscode.CancellationToken): Promise<T> {
        if (!vscode.workspace.isTrusted) {
            throw new Error('Trust this workspace before running the configured Dynamo Diff interpreter.');
        }
        if (token?.isCancellationRequested) { throw new vscode.CancellationError(); }
        const config = vscode.workspace.getConfiguration('dynamoDiff');
        const python = config.get<string>('pythonPath', 'python3');
        const store = config.get<string>('storePath') || vscode.Uri.joinPath(this.context.storageUri ?? this.context.globalStorageUri, 'captures').fsPath;
        const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        return new Promise<T>((resolve, reject) => {
            // execFile preserves argument boundaries; no shell or trace content is executed.
            const child = execFile(python, ['-m', 'dynamo_diff.cli', '--store', store, ...args],
                { cwd, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024, timeout: 180_000 },
                (error, stdout, stderr) => {
                    cancellation?.dispose();
                    if (token?.isCancellationRequested) { reject(new vscode.CancellationError()); return; }
                    if (error) {
                        let message = stderr.trim() || error.message;
                        try { const parsed = JSON.parse(stderr); message = `${parsed.error.code}: ${parsed.error.message}`; } catch { /* preserve readable failure */ }
                        reject(new Error(message.slice(0, 3000))); return;
                    }
                    try { resolve(JSON.parse(stdout) as T); }
                    catch { reject(new Error('Dynamo Diff returned invalid JSON. Check the configured Python installation.')); }
                });
            const cancellation = token?.onCancellationRequested(() => child.kill('SIGTERM'));
        });
    }
}

class Item extends vscode.TreeItem {
    constructor(label: string, public readonly children: Item[] = []) {
        super(label, children.length ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.None);
    }
}

class Results implements vscode.TreeDataProvider<Item> {
    private readonly changed = new vscode.EventEmitter<Item | undefined>();
    readonly onDidChangeTreeData = this.changed.event;
    report?: Comparison;
    roots: Item[] = [];

    getTreeItem(item: Item): vscode.TreeItem { return item; }
    getChildren(item?: Item): Item[] { return item?.children ?? this.roots; }

    set(report: Comparison): void {
        this.report = report;
        const overview = new Item(`Workload: ${report.workload_comparability.replaceAll('_', ' ')}`, [
            new Item(`Baseline artifacts: ${report.capture_validity.baseline.artifact_structure}; workload completion: ${report.capture_validity.baseline.workload_completion}`),
            new Item(`Candidate artifacts: ${report.capture_validity.candidate.artifact_structure}; workload completion: ${report.capture_validity.candidate.workload_completion}`),
            new Item(`Completed compilations: ${report.baseline_counts.completed} → ${report.candidate_counts.completed}`),
            new Item(`Confirmed recompilations: ${report.baseline_counts.confirmed_successful_recompilations} → ${report.candidate_counts.confirmed_successful_recompilations}`),
            new Item('Application performance: not measured'),
            ...report.notices.map(n => { const item = new Item(n.message); item.tooltip = n.code; item.iconPath = new vscode.ThemeIcon('info'); return item; })
        ]);
        overview.collapsibleState = vscode.TreeItemCollapsibleState.Expanded;
        const rows = report.functions.map(row => {
            const group = (row.candidate.length ? row.candidate : row.baseline)[0];
            const name = group.source.qualified_name ?? group.source.function ?? 'Unknown function';
            const item = new Item(name, [
                new Item(`Source match: ${row.match_status} (${row.match_method.replaceAll('_', ' ')})`),
                ...this.side('Baseline', report.baseline_id, row.baseline),
                ...this.side('Candidate', report.candidate_id, row.candidate)
            ]);
            item.description = `${row.baseline_counts.confirmed_successful_recompilations} → ${row.candidate_counts.confirmed_successful_recompilations} recompiles · ${row.match_status}`;
            item.tooltip = `${group.source.relative_path ?? group.source.captured_path ?? 'Source unavailable'}\nCompleted: ${row.baseline_counts.completed} → ${row.candidate_counts.completed}\nMatch status describes correspondence, not an optimization verdict.`;
            item.iconPath = new vscode.ThemeIcon(row.match_status === 'ambiguous' ? 'question' : 'symbol-function');
            return item;
        });
        this.roots = [overview, ...rows];
        this.changed.fire(undefined);
    }

    private side(label: string, captureId: string, groups: Group[]): Item[] {
        return groups.map(group => {
            const source = new Item('Open captured source');
            source.iconPath = new vscode.ThemeIcon('file-code');
            source.command = { command: 'dynamoDiff.openSource', title: 'Open captured source', arguments: [{ captureId, functionId: group.id }] };
            const evidence = group.evidence_ids.map(evidenceId => {
                const item = new Item(evidenceId);
                item.command = { command: 'dynamoDiff.openEvidence', title: 'Open evidence', arguments: [{ captureId, evidenceId }] };
                item.iconPath = new vscode.ThemeIcon('references');
                return item;
            });
            return new Item(`${label}: ${group.counts.completed} completed, ${group.counts.confirmed_successful_recompilations} confirmed recompiles`, [
                source,
                new Item(`Guard categories: ${group.guard_categories.join(', ') || 'none recorded'}`),
                new Item(`Failures: ${group.counts.failed}; no graph: ${group.counts.no_graph_observed}; unknown: ${group.counts.unknown_outcomes}`),
                new Item('Evidence', evidence)
            ]);
        });
    }

    dispose(): void { this.changed.dispose(); }
}

class Documents implements vscode.TextDocumentContentProvider {
    readonly values = new Map<string, string>();
    provideTextDocumentContent(uri: vscode.Uri): string { return this.values.get(uri.toString()) ?? 'This captured view is no longer available. Reopen it from Dynamo Diff.'; }

    async open(kind: string, key: string, filename: string, text: string, language: string, line?: number): Promise<vscode.TextEditor> {
        const uri = vscode.Uri.from({ scheme: 'dynamo-diff', path: `/${kind}/${key}/${path.basename(filename)}` });
        this.values.set(uri.toString(), text);
        let document = await vscode.workspace.openTextDocument(uri);
        document = await vscode.languages.setTextDocumentLanguage(document, language);
        const editor = await vscode.window.showTextDocument(document, { preview: true, viewColumn: vscode.ViewColumn.Active });
        if (line) {
            const position = new vscode.Position(Math.max(0, Math.min(line - 1, document.lineCount - 1)), 0);
            editor.selection = new vscode.Selection(position, position);
            editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenterIfOutsideViewport);
        }
        return editor;
    }
}

export function activate(context: vscode.ExtensionContext) {
    const runner = new Runner(context);
    const results = new Results();
    const documents = new Documents();
    const view = vscode.window.createTreeView('dynamoDiff.results', { treeDataProvider: results, showCollapseAll: true });
    context.subscriptions.push(view, results, vscode.workspace.registerTextDocumentContentProvider('dynamo-diff', documents),
        vscode.workspace.onDidCloseTextDocument(document => documents.values.delete(document.uri.toString())));
    let captures = context.workspaceState.get<SavedCapture[]>('captures', []);

    const register = (name: string, action: (...args: any[]) => Promise<unknown>) => {
        context.subscriptions.push(vscode.commands.registerCommand(name, async (...args: any[]) => {
            try { return await action(...args); }
            catch (error) {
                if (error instanceof vscode.CancellationError) { return undefined; }
                const message = error instanceof Error ? error.message : String(error);
                void vscode.window.showErrorMessage(`Dynamo Diff: ${message}`);
                throw error;
            }
        }));
    };

    register('dynamoDiff.importCapture', async (input?: { reportPath: string; manifestPath?: string }) => {
        let reportPath = input?.reportPath;
        let manifestPath = input?.manifestPath;
        if (!reportPath) {
            const selected = await vscode.window.showOpenDialog({ canSelectFolders: true, canSelectFiles: false, canSelectMany: false, openLabel: 'Import tlparse report' });
            if (!selected?.length) { return; }
            reportPath = selected[0].fsPath;
            const choice = await vscode.window.showQuickPick(['Choose a run manifest', 'Import without a manifest'], { title: 'Run metadata', placeHolder: 'A manifest enables workload checks and captured-source navigation.' });
            if (!choice) { return; }
            if (choice === 'Choose a run manifest') {
                const manifest = await vscode.window.showOpenDialog({ canSelectFiles: true, canSelectFolders: false, canSelectMany: false, filters: { JSON: ['json'] }, openLabel: 'Use manifest' });
                if (!manifest?.length) { return; }
                manifestPath = manifest[0].fsPath;
            }
        }
        const args = ['import', reportPath, ...(manifestPath ? ['--manifest', manifestPath] : [])];
        const receipt = await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Importing Dynamo capture', cancellable: true },
            (_, token) => runner.run<Receipt>(args, token));
        const label = path.basename(path.dirname(reportPath)) + ' / ' + path.basename(reportPath);
        captures = [{ id: receipt.capture_id, label }, ...captures.filter(c => c.id !== receipt.capture_id)].slice(0, 100);
        await context.workspaceState.update('captures', captures);
        void vscode.window.showInformationMessage(`Imported ${label}: ${receipt.counts.completed} completed compilations, ${receipt.counts.confirmed_successful_recompilations} confirmed recompilations.`);
        return receipt;
    });

    register('dynamoDiff.compareCaptures', async (input?: { baselineId: string; candidateId: string }) => {
        let baselineId = input?.baselineId;
        let candidateId = input?.candidateId;
        if (!baselineId || !candidateId) {
            const options = captures.map(c => ({ label: c.label, description: c.id.slice(0, 12), id: c.id }));
            if (options.length < 2) { throw new Error('Import two captures before comparing.'); }
            const baseline = await vscode.window.showQuickPick(options, { title: 'Choose baseline capture' });
            if (!baseline) { return; }
            const candidate = await vscode.window.showQuickPick(options.filter(c => c.id !== baseline.id), { title: 'Choose candidate capture' });
            if (!candidate) { return; }
            baselineId = baseline.id; candidateId = candidate.id;
        }
        const report = await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Comparing Dynamo captures', cancellable: true },
            (_, token) => runner.run<Comparison>(['compare', baselineId!, candidateId!, '--format', 'json'], token));
        results.set(report);
        await vscode.commands.executeCommand('dynamoDiff.results.focus');
        return report;
    });

    register('dynamoDiff.openSource', async (input: { captureId: string; functionId: string }) => {
        if (!input?.captureId || !input?.functionId) { throw new Error('Choose Open captured source under a function in the Dynamo Diff results.'); }
        const source = await runner.run<SourceResult>(['source', input.captureId, input.functionId]);
        await documents.open('source', `${input.captureId}/${encodeURIComponent(input.functionId)}`, source.relative_path ?? 'captured.py', source.text, 'python', source.first_line ?? undefined);
        return source;
    });

    register('dynamoDiff.openEvidence', async (input: { captureId: string; evidenceId: string; offset?: number }) => {
        if (!input?.captureId || !input?.evidenceId) { throw new Error('Choose an evidence entry under a function in the Dynamo Diff results.'); }
        const evidence = await runner.run<EvidenceResult>(['evidence', input.captureId, input.evidenceId, '--offset', String(input.offset ?? 0)]);
        const text = `Captured compiler evidence\nSHA-256: ${evidence.sha256}\nArtifact: ${evidence.artifact}\nRecord: ${evidence.record_line ?? 'n/a'}\n\n${evidence.text}\n${evidence.truncated ? `\nExcerpt ends at offset ${evidence.next_offset} of ${evidence.total_chars} characters.` : ''}`;
        await documents.open('evidence', input.captureId, `${input.evidenceId}-${input.offset ?? 0}.txt`, text, 'plaintext');
        if (evidence.truncated) {
            void vscode.window.showInformationMessage('This evidence excerpt continues.', 'Open next excerpt').then(choice => {
                if (choice) { void vscode.commands.executeCommand('dynamoDiff.openEvidence', { ...input, offset: evidence.next_offset }); }
            });
        }
        return evidence;
    });

    register('dynamoDiff.showReport', async () => {
        if (!results.report) { throw new Error('Compare two captures to create a report.'); }
        return documents.open('report', results.report.id, 'comparison.json', JSON.stringify(results.report, null, 2), 'json');
    });

    register('dynamoDiff.showTable', async () => {
        if (!results.report) { throw new Error('Compare two captures to create a table.'); }
        const editor = await documents.open('table', results.report.id, 'comparison.md', comparisonTable(results.report), 'markdown');
        await vscode.commands.executeCommand('markdown.showPreview', editor.document.uri);
        return editor.document.getText();
    });

    return { getReport: () => results.report, getRootItems: () => results.roots };
}

export function deactivate(): void { /* VS Code disposes registered resources. */ }
