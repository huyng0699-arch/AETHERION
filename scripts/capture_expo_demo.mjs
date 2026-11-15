/* Capture the real Expo web export, backed by an isolated local Server.
 * Run after installing Playwright in apps/mobile and starting
 * `python scripts/run_mobile_local.py --verification`.
 */
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'apps', 'mobile', 'package.json'));
const { chromium } = require('playwright');
const url = process.env.AETHERION_BASE_URL || 'http://127.0.0.1:8769';
const output = path.resolve(process.env.AETHERION_SCREENSHOT_DIR || path.join(root, '.runtime', 'mobile-demo'));
await mkdir(output, { recursive: true });

const archive = JSON.parse(await readFile(path.join(root, 'apps', 'mobile', 'assets', 'ma7_source.json'), 'utf8'));
const access = JSON.parse(await readFile(path.join(root, '.runtime', 'verification-access.json'), 'utf8'));
assert.equal(access.url, url, 'Use the isolated verification Server for screenshots');
const sourceResponse = await fetch(`${url}/api/v1/demo/nasa-ma7`);
assert.equal(sourceResponse.status, 200, 'NASA archive endpoint must be available');
assert.deepEqual(await sourceResponse.json(), archive, 'Server and app archive must agree');

const browser = await chromium.launch({ headless: true });
const errors = [];
const screenshots = [];

async function capture(name, width, height, mobile) {
  const context = await browser.newContext({ viewport: { width, height }, isMobile: mobile, deviceScaleFactor: 1 });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(`${name}: ${error.message}`));
  const shot = async label => {
    const filename = `${name}-${label}.png`;
    await page.screenshot({ path: path.join(output, filename), fullPage: true, animations: 'disabled' });
    screenshots.push(filename);
  };
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    const demo = page.getByRole('button', { name: 'Demo', exact: true });
    await demo.waitFor({ state: 'visible', timeout: 30000 });
    await page.waitForFunction(() => [...document.fonts].some(font => /ionicons/i.test(font.family) && font.status === 'loaded'));
    await page.waitForFunction(() => [...document.images].every(image => image.complete && image.naturalWidth > 0));
    await page.getByLabel('Username', { exact: true }).waitFor({ state: 'visible' });
    await page.getByLabel('Password', { exact: true }).waitFor({ state: 'visible' });
    const bounds = await demo.boundingBox();
    assert.ok(bounds && bounds.y >= 0 && bounds.y + bounds.height <= height, `${name}: Demo should be visible on login`);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `${name}: unexpected horizontal page overflow`);
    await shot('login');

    await demo.click();
    const explore = page.getByRole('button', { name: 'Explore data', exact: true });
    await explore.waitFor({ state: 'visible' });
    await shot('demo-introduction');
    await explore.click();
    await page.getByRole('tab', { name: 'Flight phases', exact: true }).waitFor({ state: 'visible' });
    await page.getByText('57', { exact: true }).first().waitFor({ state: 'visible' });
    await page.getByText('beats/min', { exact: true }).first().waitFor({ state: 'visible' });
    await shot('nasa-data');
    await page.getByRole('tab', { name: 'Blood count', exact: true }).click();
    await shot('blood-count');

    await page.getByRole('button', { name: 'Back', exact: true }).click();
    await explore.waitFor({ state: 'visible' });
    await page.getByRole('button', { name: 'Back', exact: true }).click();
    await demo.waitFor({ state: 'visible' });
    await page.getByLabel('Username', { exact: true }).fill(access.username);
    await page.getByLabel('Password', { exact: true }).fill(access.password);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await page.getByRole('button', { name: 'Library', exact: true }).first().waitFor({ state: 'visible' });
    await shot('home');
    await page.getByRole('button', { name: 'Library', exact: true }).first().click();
    await page.getByRole('button', { name: 'Back', exact: true }).waitFor({ state: 'visible' });
    await page.getByText(/NASA/i).first().waitFor({ state: 'visible' });
    await shot('library');
    console.log(`PASS ${name}: login, Demo, NASA values, navigation, sign-in and Library`);
  } catch (error) {
    await shot('failure').catch(() => {});
    throw error;
  } finally {
    await context.close();
  }
}

try {
  await capture('phone', 390, 844, true);
  await capture('small-phone', 320, 740, true);
  await capture('desktop', 1440, 900, false);
  assert.deepEqual(errors, [], 'Unexpected JavaScript exceptions');
  await writeFile(path.join(output, 'result.json'), JSON.stringify({ status: 'PASS', screenshots }, null, 2));
} finally {
  await browser.close();
}
