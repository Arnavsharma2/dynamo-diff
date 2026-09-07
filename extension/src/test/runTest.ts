import { downloadAndUnzipVSCode, resolveCliArgsFromVSCodeExecutablePath, runTests } from '@vscode/test-electron';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createHash } from 'node:crypto';
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import * as os from 'node:os';

async function main(): Promise<void> {
    const extensionRoot = path.resolve(__dirname, '../..');
    const projectRoot = path.dirname(extensionRoot);
    const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'dynamo-diff-editor-'));
    const workspace = path.join(temporary, 'workspace with spaces');
    const userData = path.join(temporary, 'user-data');
    const extensionsDir = path.join(temporary, 'extensions');
    const vsix = process.env.DYNAMO_DIFF_VSIX;
    await fs.mkdir(path.join(workspace, '.vscode'), { recursive: true });
    await fs.mkdir(path.join(userData, 'User'), { recursive: true });
    const python = process.env.DYNAMO_DIFF_PYTHON || path.join(projectRoot, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
    const resultPath = process.env.DYNAMO_DIFF_TEST_RESULT;
    if (resultPath) {
        await fs.mkdir(path.dirname(resultPath), { recursive: true });
        await fs.writeFile(resultPath, JSON.stringify({ status: 'running', started_at: new Date().toISOString() }, null, 2) + '\n');
    }
    await fs.writeFile(path.join(workspace, '.vscode/settings.json'), JSON.stringify({
        'dynamoDiff.pythonPath': python,
        'dynamoDiff.storePath': path.join(temporary, 'capture store'),
    }));
    await fs.writeFile(path.join(userData, 'User/settings.json'), JSON.stringify({
        'telemetry.telemetryLevel': 'off', 'update.mode': 'none',
        'chat.disableAIFeatures': true,
        'extensions.autoUpdate': false, 'extensions.autoCheckUpdates': false,
        'workbench.startupEditor': 'none', 'window.restoreWindows': 'none',
        'security.workspace.trust.enabled': false,
    }));
    try {
        let executable = process.env.VSCODE_EXECUTABLE_PATH;
        let developmentPath = extensionRoot;
        let vsixSha256: string | undefined;
        let installedMainSha256: string | undefined;
        if (vsix) {
            if (process.platform === 'win32') { throw new Error('Packaged-extension harness currently supports macOS/Linux'); }
            executable ||= await downloadAndUnzipVSCode('1.132.1');
            vsixSha256 = createHash('sha256').update(await fs.readFile(vsix)).digest('hex');
            installedMainSha256 = createHash('sha256').update(await fs.readFile(path.join(extensionRoot, 'out/extension.js'))).digest('hex');
            // The resolver supplies only the CLI executable; both profile locations below are temporary.
            const [cli, ...args] = resolveCliArgsFromVSCodeExecutablePath(executable, { reuseMachineInstall: true });
            const installation = await promisify(execFile)(cli, [...args,
                '--user-data-dir', userData, '--extensions-dir', extensionsDir,
                '--install-extension', path.resolve(vsix), '--force'], { timeout: 120_000 });
            console.log(installation.stdout);
            // Tests run from a separate helper, so a development copy cannot shadow the installed VSIX.
            developmentPath = path.join(temporary, 'test-driver');
            await fs.mkdir(developmentPath);
            await fs.writeFile(path.join(developmentPath, 'package.json'), JSON.stringify({
                name: 'dynamo-diff-test-driver', publisher: 'test-driver', version: '0.0.0',
                engines: { vscode: '^1.100.0' }, main: './index.js', activationEvents: ['*'],
            }));
            await fs.writeFile(path.join(developmentPath, 'index.js'), 'exports.activate = () => {};\n');
        }
        await runTests({
            extensionDevelopmentPath: developmentPath,
            extensionTestsPath: path.join(__dirname, 'suite/index'),
            vscodeExecutablePath: executable,
            version: '1.132.1',
            reuseMachineInstall: false,
            launchArgs: [workspace, '--user-data-dir', userData,
                '--extensions-dir', extensionsDir, ...(vsix ? [] : ['--disable-extensions']),
                '--skip-welcome', '--skip-release-notes', '--disable-workspace-trust'],
            extensionTestsEnv: {
                DYNAMO_DIFF_PROJECT: projectRoot, DYNAMO_DIFF_TEST_TEMP: temporary,
                DYNAMO_DIFF_PYTHON: python,
                DYNAMO_DIFF_TEST_RESULT: process.env.DYNAMO_DIFF_TEST_RESULT,
                DYNAMO_DIFF_EXPECT_INSTALLED: vsix ? '1' : undefined,
                DYNAMO_DIFF_VSIX_SHA256: vsixSha256,
                DYNAMO_DIFF_EXPECTED_MAIN_SHA256: installedMainSha256,
            },
        });
    } catch (error) {
        if (resultPath) {
            await fs.writeFile(resultPath, JSON.stringify({ status: 'failed', error: String(error), finished_at: new Date().toISOString() }, null, 2) + '\n');
        }
        throw error;
    } finally {
        await fs.rm(temporary, { recursive: true, force: true });
    }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
