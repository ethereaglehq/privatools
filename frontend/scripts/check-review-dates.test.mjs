import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkRepo, compareReviewDates, hasBulkMarker } from './check-review-dates.mjs';

const tool = (slug, overrides = {}) => ({
  slug,
  name: slug,
  description: `${slug} in one line`,
  longDescription: `${slug} explained at length.`,
  seoTitle: `${slug} search title`,
  metaDescription: `${slug} meta description.`,
  synonyms: 'alpha beta',
  lastReviewed: '2026-09-01',
  ...overrides,
});
const pdf = (slug, overrides) => ({ ...tool(slug, overrides), path: `/tool/${slug}` });
const many = (count, overrides, make = pdf) => Array.from({ length: count }, (_, index) => make(`tool-${index + 1}`, overrides));

// ── The comparison ───────────────────────────────────────────────────────────

test('accepts a registry that did not change', () => {
  const result = compareReviewDates([pdf('merge-pdf')], [pdf('merge-pdf')]);
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.moved, []);
});

for (const field of ['seoTitle', 'metaDescription', 'longDescription', 'description']) {
  test(`fails when ${field} changes and lastReviewed stays`, () => {
    const result = compareReviewDates([pdf('merge-pdf')], [pdf('merge-pdf', { [field]: 'Rewritten.' })]);
    assert.deepEqual(result.stale, [{ path: '/tool/merge-pdf', fields: [field] }]);
    assert.equal(result.errors.length, 1);
    assert.match(result.errors[0], /\/tool\/merge-pdf/);
  });
}

test('reports a tool once, with every copy field that changed', () => {
  const result = compareReviewDates([pdf('merge-pdf')], [pdf('merge-pdf', { seoTitle: 'New title', description: 'New line' })]);
  assert.deepEqual(result.stale, [{ path: '/tool/merge-pdf', fields: ['seoTitle', 'description'] }]);
  assert.equal(result.errors.length, 1);
});

test('accepts changed copy when lastReviewed moves with it', () => {
  const result = compareReviewDates([pdf('merge-pdf')], [pdf('merge-pdf', { longDescription: 'Rewritten.', lastReviewed: '2026-09-18' })]);
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.moved, ['/tool/merge-pdf']);
});

test('ignores fields that are not page or search copy', () => {
  const result = compareReviewDates([pdf('merge-pdf')], [pdf('merge-pdf', { synonyms: 'join combine', popularity: 3 })]);
  assert.deepEqual(result.errors, []);
});

test('does not count new tools as moved dates', () => {
  const result = compareReviewDates([pdf('merge-pdf')], [pdf('merge-pdf'), ...many(30, { lastReviewed: '2026-09-18' })]);
  assert.deepEqual(result.moved, []);
  assert.equal(result.firstDated.length, 30);
  assert.deepEqual(result.errors, []);
});

test('does not count a date introduced on an existing tool as moved', () => {
  const undated = many(30).map(({ lastReviewed, seoTitle, metaDescription, ...legacy }) => legacy);
  const result = compareReviewDates(undated, many(30, { lastReviewed: '2026-09-18' }));
  assert.deepEqual(result.moved, []);
  assert.equal(result.firstDated.length, 30);
  assert.deepEqual(result.errors, []);
});

test('ignores tools removed from the registry', () => {
  const result = compareReviewDates([pdf('merge-pdf'), pdf('retired-tool')], [pdf('merge-pdf')]);
  assert.deepEqual(result.errors, []);
});

test('accepts a date that moves on its own, without any copy change', () => {
  const result = compareReviewDates([pdf('merge-pdf')], [pdf('merge-pdf', { lastReviewed: '2026-09-18' })]);
  assert.deepEqual(result.moved, ['/tool/merge-pdf']);
  assert.deepEqual(result.errors, []);
});

test('allows 25 moved dates in one change', () => {
  const result = compareReviewDates(many(25), many(25, { lastReviewed: '2026-09-18' }));
  assert.equal(result.moved.length, 25);
  assert.deepEqual(result.errors, []);
});

test('fails on 26 moved dates without the bulk marker', () => {
  const result = compareReviewDates(many(26), many(26, { lastReviewed: '2026-09-18' }));
  assert.equal(result.moved.length, 26);
  assert.equal(result.errors.length, 1);
  assert.match(result.errors[0], /\[bulk-review\]/);
});

test('allows 26 moved dates in a marked bulk review', () => {
  const result = compareReviewDates(many(26), many(26, { lastReviewed: '2026-09-18' }), { bulkAllowed: true });
  assert.deepEqual(result.errors, []);
});

test('a marked bulk review still fails on copy whose date stayed', () => {
  const head = [...many(26, { lastReviewed: '2026-09-18' }), pdf('merge-pdf', { seoTitle: 'Rewritten' })];
  const result = compareReviewDates([...many(26), pdf('merge-pdf')], head, { bulkAllowed: true });
  assert.deepEqual(result.stale, [{ path: '/tool/merge-pdf', fields: ['seoTitle'] }]);
  assert.equal(result.errors.length, 1);
});

test('keeps the same slug in the two registries apart', () => {
  const other = (slug, overrides) => ({ ...tool(slug, overrides), path: `/tools/${slug}` });
  const base = [pdf('compress', { description: 'Shrink a PDF' }), other('compress', { description: 'Shrink an image' })];
  const head = [pdf('compress', { description: 'Shrink a PDF' }), other('compress', { description: 'Shrink a photo' })];
  assert.deepEqual(compareReviewDates(base, head).stale, [{ path: '/tools/compress', fields: ['description'] }]);
});

// Only a marker that starts a line counts, so explaining the flag in prose
// cannot switch it on. The second `false` row is this check's own first commit
// message, which did exactly that while any mention counted.
test('accepts the bulk marker only as the first text on a line', () => {
  const cases = [
    ['[bulk-review] Re-read every tool', true],
    ['   [bulk-review] Re-read every tool', true],
    ['Re-read every tool\n\n[bulk-review] each page was checked against the live tool', true],
    ['Re-read every tool\n\n  [bulk-review]', true],
    ['Re-read every tool [bulk-review]', false],
    ['Add the guard\n\nA real bulk review opts in with [bulk-review] in a commit message.', false],
    ['Add the guard\n\n`[bulk-review]` opts a real bulk review in.', false],
    ['Bulk review of every tool\n\nbulk-review', false],
  ];
  for (const [text, expected] of cases) assert.equal(hasBulkMarker([text]), expected, JSON.stringify(text));
  assert.equal(hasBulkMarker(['Fix a typo', '[bulk-review] Re-read every tool']), true);
  assert.equal(hasBulkMarker([undefined, '']), false);
});

// ── Against a real repository ────────────────────────────────────────────────

const SCRIPT = fileURLToPath(new URL('./check-review-dates.mjs', import.meta.url));
// A developer's global identity, signing or hooks must not decide these tests.
const GIT_OPTIONS = ['-c', 'user.name=Review Dates Test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null'];
const git = (cwd, ...args) => execFileSync('git', [...GIT_OPTIONS, ...args], { cwd, encoding: 'utf8' }).trim();

// Shaped like the real registries: a type annotation, and an icon identifier
// that is not a literal and has to be skipped rather than parsed.
const registrySource = (variable, tools) => `import { FileIcon } from "lucide-react";
const ${variable}: Tool[] = [
${tools.map(({ slug, ...rest }) => `  { slug: ${JSON.stringify(slug)}, icon: FileIcon, ${Object.entries(rest).map(([key, value]) => `${key}: ${JSON.stringify(value)}`).join(', ')} },`).join('\n')}
];
`;

function writeRegistries(root, pdfTools, otherTools) {
  const dir = join(root, 'frontend/src/data');
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'tools.ts'), registrySource('_toolsRaw', pdfTools));
  writeFileSync(join(dir, 'non-pdf-tools.ts'), registrySource('_nonPdfToolsRaw', otherTools));
}

function commit(root, message) {
  git(root, 'add', '-A');
  git(root, 'commit', '-q', '-m', message);
}

// Leaves the repository on a `feature` branch cut from the first commit on `main`.
function makeRepo(t, pdfTools, otherTools, baseMessage = 'Add the registries') {
  const root = mkdtempSync(join(tmpdir(), 'review-dates-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  git(root, 'init', '-q', '-b', 'main');
  writeRegistries(root, pdfTools, otherTools);
  commit(root, baseMessage);
  git(root, 'checkout', '-q', '-b', 'feature');
  return root;
}

const plain = (count, overrides) => many(count, overrides, tool);

test('reads the base from git and the head from the working tree, in both registries', t => {
  const root = makeRepo(t, [tool('merge-pdf')], [tool('resize-image')]);
  writeRegistries(root, [tool('merge-pdf', { seoTitle: 'Rewritten' })], [tool('resize-image', { description: 'Rewritten', lastReviewed: '2026-09-18' })]);
  const result = checkRepo({ root, baseRef: 'main' });
  assert.equal(result.compared, 2);
  assert.deepEqual(result.stale, [{ path: '/tool/merge-pdf', fields: ['seoTitle'] }]);
  assert.deepEqual(result.moved, ['/tools/resize-image']);
});

test('measures a branch from where it left the base, not from the base tip', t => {
  const root = makeRepo(t, plain(30), []);
  git(root, 'checkout', '-q', 'main');
  writeRegistries(root, plain(30, { lastReviewed: '2026-09-18' }), []);
  commit(root, '[bulk-review] Re-read every tool');
  git(root, 'checkout', '-q', 'feature');
  const result = checkRepo({ root, baseRef: 'main' });
  assert.deepEqual(result.moved, []);
  assert.deepEqual(result.errors, []);
});

test('accepts the bulk marker at the start of a commit body line', t => {
  const root = makeRepo(t, plain(26), []);
  writeRegistries(root, plain(26, { lastReviewed: '2026-09-18' }), []);
  commit(root, 'Re-read every tool\n\n[bulk-review] each page was checked against the live tool');
  assert.deepEqual(checkRepo({ root, baseRef: 'main' }).errors, []);
});

test('does not accept the bulk marker mid-sentence in a commit message', t => {
  const root = makeRepo(t, plain(26), []);
  writeRegistries(root, plain(26, { lastReviewed: '2026-09-18' }), []);
  commit(root, 'Bump every date\n\nA real bulk review opts in with [bulk-review] in a commit message.');
  const { errors } = checkRepo({ root, baseRef: 'main' });
  assert.equal(errors.length, 1);
  assert.match(errors[0], /moved on 26 tools/);
});

test('does not accept a bulk marker that is already in the base history', t => {
  const root = makeRepo(t, plain(26), [], '[bulk-review] Add the registries');
  writeRegistries(root, plain(26, { lastReviewed: '2026-09-18' }), []);
  commit(root, 'Bump every date');
  const result = checkRepo({ root, baseRef: 'main' });
  assert.equal(result.moved.length, 26);
  assert.equal(result.errors.length, 1);
});

test('accepts the bulk marker at the start of the PR title', t => {
  const root = makeRepo(t, plain(26), []);
  writeRegistries(root, plain(26, { lastReviewed: '2026-09-18' }), []);
  commit(root, 'Re-read every tool');
  assert.deepEqual(checkRepo({ root, baseRef: 'main', prTitle: '[bulk-review] Re-read every tool' }).errors, []);
});

test('does not accept the bulk marker mid-sentence in the PR title', t => {
  const root = makeRepo(t, plain(26), []);
  writeRegistries(root, plain(26, { lastReviewed: '2026-09-18' }), []);
  commit(root, 'Re-read every tool');
  const { errors } = checkRepo({ root, baseRef: 'main', prTitle: 'Re-read every tool [bulk-review]' });
  assert.equal(errors.length, 1);
  assert.match(errors[0], /moved on 26 tools/);
});

// The field was added to every tool at once, so any base older than that
// commit has none. Those 221 first dates must not read as a bulk bump.
test('passes against a base whose registries have no lastReviewed at all', t => {
  const undated = plain(30).map(({ lastReviewed, ...older }) => older);
  const root = makeRepo(t, undated, []);
  writeRegistries(root, plain(30, { lastReviewed: '2026-09-18' }), []);
  const result = checkRepo({ root, baseRef: 'main' });
  assert.equal(result.firstDated.length, 30);
  assert.deepEqual(result.moved, []);
  assert.deepEqual(result.errors, []);
});

test('passes on the base branch itself, where there is nothing to compare', t => {
  const root = makeRepo(t, plain(30), []);
  git(root, 'checkout', '-q', 'main');
  const result = checkRepo({ root, baseRef: 'main' });
  assert.equal(result.compared, 30);
  assert.deepEqual(result.moved, []);
  assert.deepEqual(result.errors, []);
});

test('refuses to pass when the base ref is unknown, and says to fetch it', t => {
  const root = makeRepo(t, [tool('merge-pdf')], []);
  assert.throws(() => checkRepo({ root, baseRef: 'origin/main' }), /fetch/);
});

// ── The command CI runs ──────────────────────────────────────────────────────

// CI sets both variables for the real run; a test must not inherit them.
function runCli(cwd, env = {}, args = []) {
  const { GITHUB_BASE_REF, PR_TITLE, ...inherited } = process.env;
  return spawnSync(process.execPath, [SCRIPT, ...args], { cwd, encoding: 'utf8', env: { ...inherited, ...env } });
}

test('exits non-zero and names the tool when copy changed without its date', t => {
  const root = makeRepo(t, [tool('merge-pdf')], []);
  git(root, 'update-ref', 'refs/remotes/origin/main', 'main');
  writeRegistries(root, [tool('merge-pdf', { metaDescription: 'Rewritten.' })], []);
  // npm runs package scripts from frontend/, not from the repository root.
  const run = runCli(join(root, 'frontend'));
  assert.equal(run.status, 1);
  assert.match(run.stderr, /\/tool\/merge-pdf/);
});

test('exits zero when the date follows the copy', t => {
  const root = makeRepo(t, [tool('merge-pdf')], []);
  git(root, 'update-ref', 'refs/remotes/origin/main', 'main');
  writeRegistries(root, [tool('merge-pdf', { metaDescription: 'Rewritten.', lastReviewed: '2026-09-18' })], []);
  const run = runCli(join(root, 'frontend'));
  assert.equal(run.status, 0, run.stderr);
});

test('takes the bulk marker from PR_TITLE', t => {
  const root = makeRepo(t, plain(26), []);
  git(root, 'update-ref', 'refs/remotes/origin/main', 'main');
  writeRegistries(root, plain(26, { lastReviewed: '2026-09-18' }), []);
  assert.equal(runCli(root).status, 1);
  assert.equal(runCli(root, { PR_TITLE: '[bulk-review] Re-read every tool' }).status, 0);
});

test('on a pull request, compares against the branch the PR targets', t => {
  const root = makeRepo(t, [tool('merge-pdf')], []);
  git(root, 'update-ref', 'refs/remotes/origin/release', 'main');
  const run = runCli(root, { GITHUB_BASE_REF: 'release' });
  assert.equal(run.status, 0, run.stderr);
});

test('takes another base ref as its argument', t => {
  const root = makeRepo(t, [tool('merge-pdf')], []);
  const run = runCli(root, {}, ['main']);
  assert.equal(run.status, 0, run.stderr);
});

test('exits non-zero rather than skipping when origin/main was never fetched', t => {
  const root = makeRepo(t, [tool('merge-pdf')], []);
  const run = runCli(root);
  assert.equal(run.status, 1);
  assert.match(run.stderr, /fetch/);
});
