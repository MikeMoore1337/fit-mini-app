import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const staticDir = path.join(root, 'backend', 'app', 'static');
const read = (...parts) => fs.readFileSync(path.join(staticDir, ...parts), 'utf8');

function luminance(hex) {
  const channels = hex.match(/[0-9a-f]{2}/gi).map((value) => Number.parseInt(value, 16) / 255);
  const linear = channels.map((value) =>
    value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
  );
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

function contrast(left, right) {
  const values = [luminance(left), luminance(right)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

test('default action colors meet WCAG AA contrast', () => {
  const css = read('styles.css');
  const darkAccent = css.match(/--accent:\s*(#[0-9a-f]{6})/i)[1].slice(1);
  const lightBlock = css.match(/:root\[data-color-scheme="light"\]\s*\{([\s\S]*?)\n\}/)[1];
  const lightAccent = lightBlock.match(/--accent:\s*(#[0-9a-f]{6})/i)[1].slice(1);
  const dangerButton = css.match(/--danger-button:\s*(#[0-9a-f]{6})/i)[1].slice(1);
  assert.ok(contrast(darkAccent, 'ffffff') >= 4.5);
  assert.ok(contrast(lightAccent, 'ffffff') >= 4.5);
  assert.ok(contrast(dangerButton, 'ffffff') >= 4.5);
});

test('mobile primary navigation stays at five destinations', () => {
  const html = read('index.html');
  const nav = html.match(/<nav class="app-bottom-nav"[\s\S]*?<\/nav>/)[0];
  assert.equal((nav.match(/app-bottom-nav__btn/g) || []).length, 5);
  assert.match(html, /id="profileCoachLink"/);
  assert.match(html, /id="profileAdminLink"/);
});

test('all local static module and stylesheet versions are synchronized', () => {
  const files = [
    'index.html',
    'coach.html',
    'admin.html',
    'js/main.js',
    'js/coach.js',
    'js/admin.js',
    'js/core/http.js',
    'js/core/ui.js',
  ];
  const versions = files.flatMap((file) => [...read(file).matchAll(/\?v=(\d+)/g)].map((m) => m[1]));
  assert.deepEqual(new Set(versions), new Set(['57']));
});

test('admin application code is external and syntax-checkable', () => {
  const html = read('admin.html');
  assert.doesNotMatch(html, /<script type="module">/);
  assert.match(html, /src="\/static\/js\/admin\.js\?v=57"/);
});

test('all admin collections expose pagination controls', () => {
  const adminHtml = read('admin.html');
  const adminJs = read('js', 'admin.js');
  for (const id of ['usersPagination', 'paymentsPagination', 'notificationsPagination', 'templatesPagination']) {
    assert.match(adminHtml, new RegExp(`id=["']${id}["']`));
  }
  assert.match(adminJs, /includeMeta:\s*true/);
  assert.match(adminJs, /X-Total-Count/);
});

test('initial bootstrap loads only the active screen', () => {
  const mainJs = read('js', 'main.js');
  const start = mainJs.indexOf('async function bootstrap()');
  const end = mainJs.indexOf('function bindUI()', start);
  const bootstrap = mainJs.slice(start, end);
  assert.ok(start >= 0 && end > start);
  assert.match(bootstrap, /loadScreenData\('today'\)/);
  assert.doesNotMatch(bootstrap, /loadExercises|loadTemplates|loadBodyMeasurements|loadNotifications/);
});

test('workout set autosaves are serialized per set', () => {
  const mainJs = read('js', 'main.js');
  assert.match(mainJs, /const setSaveInFlight = new Map\(\)/);
  assert.match(mainJs, /while \(pendingSetPayloads\.has\(setId\)\)/);
  assert.match(mainJs, /setSaveInFlight\.set\(setId, savePromise\)/);
});
