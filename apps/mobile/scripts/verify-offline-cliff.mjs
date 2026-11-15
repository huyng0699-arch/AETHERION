import { readdir, readFile } from 'node:fs/promises';
import { resolve, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const mobileRoot = resolve(fileURLToPath(new URL('..', import.meta.url)));
const recordsDir = resolve(mobileRoot, 'assets/nasa-cliff-119/records');
const loaderPath = resolve(mobileRoot, 'src/api/offlineCliff.ts');
const allNames = await readdir(recordsDir);
const jsonNames = allNames.filter(name => name.toLowerCase().endsWith('.json')).sort();
const expected = Array.from({ length: 118 }, (_, index) => 'CLIFF-' + String(index + 1).padStart(3, '0') + '.json');
if (jsonNames.length !== 118 || jsonNames.some((name, index) => name !== expected[index])) {
  throw new Error('Expected exactly CLIFF-001 through CLIFF-118; found ' + jsonNames.length + ' JSON files.');
}
if (allNames.includes('CLIFF-119.json')) throw new Error('CLIFF-119 has no verified source and must not be bundled.');

const loader = await readFile(loaderPath, 'utf8');
const references = [...loader.matchAll(/require\(['"]\.\.\/\.\.\/assets\/nasa-cliff-119\/records\/(CLIFF-\d{3}\.json)['"]\)/g)].map(match => match[1]).sort();
if (references.length !== 118 || references.some((name, index) => name !== expected[index])) {
  throw new Error('Metro must statically include each of the 118 packaged CliFF JSON files exactly once.');
}
let bytes = 0;
for (const name of expected) {
  const file = resolve(recordsDir, name);
  const record = JSON.parse(await readFile(file, 'utf8'));
  const id = basename(name, '.json');
  if (record.article_id !== id || !Array.isArray(record.sections) || !record.source?.content_sha256) {
    throw new Error('Invalid source record shape: ' + id);
  }
  bytes += Buffer.byteLength(await readFile(file));
}
console.log('Validated bundled inventory and JSON shape: 118 CliFF records (' + bytes + ' bytes). This does not verify source PDF integrity; CLIFF-119 is absent.');
