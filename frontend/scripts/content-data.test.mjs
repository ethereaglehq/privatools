import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseContentArray } from './content-data.mjs';

test('keeps HTML, escaped quotes, sources and dates attached to the correct record', () => {
  const source = 'export const posts = [{slug:"one", title:"A \\"quote\\"", body:`<pre>{ x: 1 }</pre>`, sources:[{label:"Docs",url:"https://example.com"}], reviewedAt:"2026-09-14"},{slug:"two", body:`second`}];';
  const posts = parseContentArray(source, 'posts');
  assert.equal(posts[0].title, 'A "quote"');
  assert.equal(posts[0].body, '<pre>{ x: 1 }</pre>');
  assert.deepEqual(posts[0].sources, [{label:'Docs',url:'https://example.com'}]);
  assert.equal(posts[0].reviewedAt, '2026-09-14');
  assert.equal(posts[1].sources, undefined);
  assert.equal(posts[1].body, 'second');
});

test('rejects dynamic execution and duplicate slugs rather than silently publishing partial content', () => {
  assert.throws(() => parseContentArray('const data=[{slug:"a",body:fetch("secret")}];', 'data'), /Non-literal/);
  assert.throws(() => parseContentArray('const data=[{slug:"a"},{slug:"a"}];', 'data'), /duplicate/);
});

test('omits explicitly non-content icon references while retaining nested text', () => {
  assert.deepEqual(parseContentArray('const data=[{slug:"pdf",icon:FileIcon,description:"PDF",tags:["PDF"]}] as const;', 'data', ['icon']), [{slug:'pdf',description:'PDF',tags:['PDF']}]);
});
