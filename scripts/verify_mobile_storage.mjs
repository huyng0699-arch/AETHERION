// Exercise the actual mobile session module with deliberately delayed native
// storage operations. This does not claim an Android device test.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'apps/mobile/package.json'));
const ts = require('typescript');
const source = fs.readFileSync(path.join(root, 'apps/mobile/src/storage/session.ts'), 'utf8');
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
const pause = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
let stored = null;
let failNext = false;
const secureStore = {
  WHEN_UNLOCKED_THIS_DEVICE_ONLY: 1,
  async getItemAsync() { return stored; },
  async setItemAsync(_key, value) {
    const data = JSON.parse(value);
    await pause(data.access_token === 'slow' ? 50 : 2);
    if (failNext) { failNext = false; throw new Error('storage unavailable'); }
    stored = value;
  },
  async deleteItemAsync() { await pause(40); stored = null; },
};
const exports = {};
vm.runInNewContext(js, { exports, require: name => name === 'react-native' ? { Platform: { OS: 'android' } } : secureStore, Promise, JSON }, { filename: 'session.ts' });
const session = token => ({ access_token: token, server_url: 'https://example.invalid', expires_at: '2099-01-01T00:00:00Z', user: { username: token } });
const checks = [];
async function check(name, run) {
  try { await run(); checks.push({ name, status: 'PASS' }); console.log('PASS ' + name); }
  catch (error) { checks.push({ name, status: 'FAIL', error: error.message }); console.log('FAIL ' + name + ': ' + error.message); }
}
await check('Overlapping sign-ins keep the latest session', async () => {
  await Promise.all([exports.writeSession(session('slow')), exports.writeSession(session('new'))]);
  assert.equal((await exports.readSession()).access_token, 'new');
});
await check('Pending logout cannot erase a newer sign-in', async () => {
  await Promise.all([exports.deleteSession(), exports.writeSession(session('newer'))]);
  assert.equal((await exports.readSession()).access_token, 'newer');
});
await check('A read waits for the pending session write', async () => {
  const write = exports.writeSession(session('slow'));
  const result = await exports.readSession();
  await write;
  assert.equal(result.access_token, 'slow');
});
await check('A failed write does not block later session operations', async () => {
  failNext = true;
  await assert.rejects(exports.writeSession(session('fail')));
  await exports.writeSession(session('recovered'));
  assert.equal((await exports.readSession()).access_token, 'recovered');
});
const report = { scope: 'Actual TypeScript session module with delayed/failing in-memory native SecureStore adapter. No physical Android assertion.', checks, passed: checks.filter(x => x.status === 'PASS').length, total: checks.length };
report.pass_percent = Math.round(100 * report.passed / report.total);
const output = path.join(root, '.runtime/verification');
fs.mkdirSync(output, { recursive: true });
fs.writeFileSync(path.join(output, 'mobile-storage-report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify({ passed: report.passed, total: report.total, pass_percent: report.pass_percent }));
process.exitCode = report.passed === report.total ? 0 : 1;
