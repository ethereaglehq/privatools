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

// ── Copy corrected again inside the same change ──────────────────────────────

// A date already inside the change cannot usefully move: a second correction on
// the day of the first has no later day to move to. `cutoff` is the day the
// change began; a day's slack before it covers the author's time zone.
const correctedAgain = (lastReviewed, cutoff) => compareReviewDates(
  [pdf('merge-pdf', { lastReviewed })],
  [pdf('merge-pdf', { longDescription: 'Corrected again.', lastReviewed })],
  { cutoff },
);

test('accepts changed copy whose unchanged date is the cutoff day', () => {
  const result = correctedAgain('2026-09-18', '2026-09-18');
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.current, ['/tool/merge-pdf']);
});

test('accepts changed copy whose unchanged date is the day before the cutoff', () => {
  const result = correctedAgain('2026-09-17', '2026-09-18');
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.current, ['/tool/merge-pdf']);
});

test('fails changed copy whose unchanged date is two days before the cutoff, with the existing message', () => {
  const result = correctedAgain('2026-09-16', '2026-09-18');
  assert.deepEqual(result.current, []);
  assert.deepEqual(result.errors, ['/tool/merge-pdf: longDescription changed but lastReviewed did not. Set it to the day this copy was reviewed.']);
});

test('counts the day before the cutoff across a year boundary', () => {
  assert.deepEqual(correctedAgain('2025-12-31', '2026-01-01').errors, []);
  assert.equal(correctedAgain('2025-12-30', '2026-01-01').errors.length, 1);
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

// An author day is set at noon UTC, so the author's own day is unambiguous. The
// committer date stays the real time, as after a rebase, so a check that read
// the committer date instead would be caught.
function commit(root, message, authorDay) {
  git(root, 'add', '-A');
  const env = authorDay ? { ...process.env, GIT_AUTHOR_DATE: `${authorDay}T12:00:00+00:00` } : process.env;
  execFileSync('git', [...GIT_OPTIONS, 'commit', '-q', '-m', message], { cwd: root, env });
}

// Leaves the repository on a `feature` branch cut from the first commit on `main`.
function makeRepo(t, pdfTools, otherTools, baseMessage = 'Add the registries', baseDay) {
  const root = mkdtempSync(join(tmpdir(), 'review-dates-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  git(root, 'init', '-q', '-b', 'main');
  writeRegistries(root, pdfTools, otherTools);
  commit(root, baseMessage, baseDay);
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

// ── When the change began ────────────────────────────────────────────────────

// Commit dates rather than the clock, so a re-run on a later day agrees. The
// committer date here is today's, which would make both tools stale.
test('dates the change from the author date of its oldest registry commit, not from today', t => {
  const root = makeRepo(t, [tool('merge-pdf', { lastReviewed: '2026-01-09' }), tool('split-pdf', { lastReviewed: '2026-01-08' })], []);
  writeRegistries(root, [tool('merge-pdf', { seoTitle: 'Corrected', lastReviewed: '2026-01-09' }), tool('split-pdf', { seoTitle: 'Corrected', lastReviewed: '2026-01-08' })], []);
  commit(root, 'Correct two titles', '2026-01-10');
  assert.deepEqual(checkRepo({ root, baseRef: 'main' }).stale, [{ path: '/tool/split-pdf', fields: ['seoTitle'] }]);
});

test('dates the change from its oldest registry commit, not its newest', t => {
  const root = makeRepo(t, [tool('merge-pdf', { lastReviewed: '2026-01-09' })], []);
  writeRegistries(root, [tool('merge-pdf', { seoTitle: 'Corrected', lastReviewed: '2026-01-09' })], []);
  commit(root, 'Correct the title', '2026-01-10');
  writeRegistries(root, [tool('merge-pdf', { seoTitle: 'Corrected', description: 'Corrected', lastReviewed: '2026-01-09' })], []);
  commit(root, 'Correct the line', '2026-01-20');
  assert.deepEqual(checkRepo({ root, baseRef: 'main' }).errors, []);
});

test('does not date the change from commits that leave the registries alone', t => {
  const root = makeRepo(t, [tool('merge-pdf', { lastReviewed: '2026-01-05' })], []);
  writeFileSync(join(root, 'README.md'), 'notes\n');
  commit(root, 'Add notes', '2026-01-01');
  writeRegistries(root, [tool('merge-pdf', { seoTitle: 'Corrected', lastReviewed: '2026-01-05' })], []);
  commit(root, 'Correct the title', '2026-01-10');
  assert.deepEqual(checkRepo({ root, baseRef: 'main' }).stale, [{ path: '/tool/merge-pdf', fields: ['seoTitle'] }]);
});

test('does not date the change from registry commits already in the base', t => {
  const root = makeRepo(t, [tool('merge-pdf', { lastReviewed: '2025-12-01' })], [], 'Add the registries', '2025-06-01');
  writeRegistries(root, [tool('merge-pdf', { seoTitle: 'Corrected', lastReviewed: '2025-12-01' })], []);
  commit(root, 'Correct the title', '2026-01-10');
  assert.deepEqual(checkRepo({ root, baseRef: 'main' }).stale, [{ path: '/tool/merge-pdf', fields: ['seoTitle'] }]);
});

// Uncommitted edits have no author date yet, so they begin today. Both days come
// from the local clock here; if midnight falls between this reading and the
// check's own, today still passes and two days ago still fails.
test('dates uncommitted edits from today', t => {
  const day = offset => {
    const date = new Date();
    date.setDate(date.getDate() + offset);
    return [date.getFullYear(), date.getMonth() + 1, date.getDate()].map(part => String(part).padStart(2, '0')).join('-');
  };
  const root = makeRepo(t, [tool('merge-pdf', { lastReviewed: day(0) }), tool('split-pdf', { lastReviewed: day(-2) })], []);
  writeRegistries(root, [tool('merge-pdf', { seoTitle: 'Corrected', lastReviewed: day(0) }), tool('split-pdf', { seoTitle: 'Corrected', lastReviewed: day(-2) })], []);
  assert.deepEqual(checkRepo({ root, baseRef: 'main' }).stale, [{ path: '/tool/split-pdf', fields: ['seoTitle'] }]);
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
