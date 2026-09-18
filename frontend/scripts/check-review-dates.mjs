// A tool's lastReviewed feeds the sitemap lastmod, the visible "Last reviewed"
// line and JSON-LD dateModified, so it has to mean that someone re-read that
// page. Two ways it stops meaning that: copy is rewritten and the date stays,
// or every date is bumped at once. This compares the registries with the point
// where the change left its base branch and fails on either.
import { execFileSync } from 'node:child_process';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseContentArray, readContentArray } from './content-data.mjs';

const COPY_FIELDS = ['seoTitle', 'metaDescription', 'longDescription', 'description'];
const BULK_LIMIT = 25;
const BULK_MARKER = '[bulk-review]';
// The same files, variables and routes gen-llms.mjs publishes from.
const REGISTRIES = [
  { file: 'frontend/src/data/tools.ts', variable: '_toolsRaw', route: '/tool/' },
  { file: 'frontend/src/data/non-pdf-tools.ts', variable: '_nonPdfToolsRaw', route: '/tools/' },
];

export const hasBulkMarker = texts => texts.some(text => text?.includes(BULK_MARKER));

// Tools are matched on `path`, since nothing stops both registries using one
// slug. A date only "moves" when the base already had one: a new tool, or the
// field arriving on an old one, is a first date rather than a bump.
export function compareReviewDates(base, head, { bulkAllowed = false } = {}) {
  const before = new Map(base.map(tool => [tool.path, tool]));
  const stale = [];
  const moved = [];
  const firstDated = [];
  let compared = 0;
  for (const tool of head) {
    const old = before.get(tool.path);
    if (!old?.lastReviewed && tool.lastReviewed) firstDated.push(tool.path);
    if (!old) continue;
    compared += 1;
    const fields = COPY_FIELDS.filter(field => tool[field] !== old[field]);
    if (tool.lastReviewed !== old.lastReviewed) {
      if (old.lastReviewed) moved.push(tool.path);
    } else if (fields.length) {
      stale.push({ path: tool.path, fields });
    }
  }
  const errors = stale.map(({ path, fields }) => `${path}: ${fields.join(', ')} changed but lastReviewed did not. Set it to the day this copy was reviewed.`);
  if (moved.length > BULK_LIMIT && !bulkAllowed) {
    errors.push(`lastReviewed moved on ${moved.length} tools in one change (limit ${BULK_LIMIT}). Move a date only when that tool's own copy changed. If every one of these pages really was re-read, put ${BULK_MARKER} in a commit message, or in the PR title before the next push.`);
  }
  return { compared, stale, moved, firstDated, errors };
}

const git = (root, ...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] });

// The head is the working tree, so the check also works before committing. The
// base is the merge base rather than the tip of baseRef: on a PR merge ref the
// two are the same commit, and on a branch that has fallen behind, the tip
// would blame the branch for dates that moved on main in the meantime.
export function checkRepo({ root, baseRef, prTitle }) {
  let base;
  try {
    base = git(root, 'merge-base', baseRef, 'HEAD').trim();
  } catch {
    throw new Error(`Cannot find where this change left ${baseRef}, so review dates were not checked. Run \`git fetch origin\` first; in CI, actions/checkout needs fetch-depth: 0.`);
  }
  const read = source => REGISTRIES.flatMap(({ file, variable, route }) => source(file, variable).map(tool => ({ ...tool, path: route + tool.slug })));
  const baseTools = read((file, variable) => parseContentArray(git(root, 'show', `${base}:${file}`), variable, ['icon']));
  const headTools = read((file, variable) => readContentArray(join(root, file), variable, ['icon']));
  const bulkAllowed = hasBulkMarker([prTitle, git(root, 'log', '--format=%B', `${base}..HEAD`)]);
  return { ...compareReviewDates(baseTools, headTools, { bulkAllowed }), base, bulkAllowed };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  // GitHub sets GITHUB_BASE_REF on pull requests only; PR_TITLE comes from the
  // workflow, as an environment variable because a title is untrusted text.
  const baseRef = process.argv[2] || (process.env.GITHUB_BASE_REF ? `origin/${process.env.GITHUB_BASE_REF}` : 'origin/main');
  try {
    const root = git(process.cwd(), 'rev-parse', '--show-toplevel').trim();
    const { compared, stale, moved, firstDated, errors, base, bulkAllowed } = checkRepo({ root, baseRef, prTitle: process.env.PR_TITLE });
    for (const error of errors) console.error(`[review-dates] ${error}`);
    console.log(`[review-dates] ${compared} tools compared with ${baseRef} (${base.slice(0, 7)}): ${moved.length} dates moved${bulkAllowed ? ` under ${BULK_MARKER}` : ''}, ${firstDated.length} dated for the first time, ${stale.length} with changed copy and an unchanged date`);
    if (errors.length) process.exitCode = 1;
  } catch (error) {
    console.error(`[review-dates] ${error.message}`);
    process.exitCode = 1;
  }
}
