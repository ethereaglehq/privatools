import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import sharp from 'sharp';
import { readContentArray } from './content-data.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = path.join(root, 'public/brand');
await mkdir(output, { recursive: true });
const shapes = readContentArray(path.join(root, 'src/components/brand/geometry.ts'), 'brandGeometry');
const paths = shapes.map(shape => `<path d="${shape.path}"/>`).join('');
const svg = (inner, box = '0 0 512 512') => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${box}">${inner}</svg>`;
const mark = color => `<g fill="${color}">${paths}</g>`;
const icon = (color = '#91B2FA', radius = 104, scale = 6.1) => svg(`<rect width="512" height="512" rx="${radius}" fill="#17181B"/><g transform="translate(${256 - 24 * scale} ${256 - 28 * scale}) scale(${scale})">${mark(color)}</g>`);
const standard = icon();
await writeFile(path.join(output, 'privatools-mark.svg'), svg(mark('currentColor'), '0 0 48 56'));
await writeFile(path.join(output, 'privatools-favicon.svg'), standard);
await writeFile(path.join(output, 'privatools-icon-play.svg'), icon('#FF9678'));
await writeFile(path.join(root, 'public/icons/icon.svg'), standard);
for (const size of [48, 96, 180, 192, 512]) {
  const png = await sharp(Buffer.from(standard)).resize(size, size).png().toBuffer();
  await writeFile(path.join(output, `privatools-icon-${size}.png`), png);
  if ([192, 512].includes(size)) await writeFile(path.join(root, `public/icons/icon-${size}.png`), png);
}
const maskable = await sharp(Buffer.from(icon('#91B2FA', 0, 4.8))).resize(512, 512).png().toBuffer();
await writeFile(path.join(root, 'public/icons/icon-maskable-512.png'), maskable);
await writeFile(path.join(output, 'privatools-icon-maskable-512.png'), maskable);
// PNG-backed ICO entries retain sharp silhouettes in older browser fallbacks.
const pngs = await Promise.all([32, 48].map(size => sharp(Buffer.from(standard)).resize(size, size).png().toBuffer()));
const header = Buffer.alloc(6 + pngs.length * 16);
header.writeUInt16LE(1, 2); header.writeUInt16LE(pngs.length, 4);
let offset = header.length;
pngs.forEach((png, index) => {
  const entry = 6 + index * 16;
  header[entry] = header[entry + 1] = [32, 48][index];
  header.writeUInt16LE(1, entry + 4); header.writeUInt16LE(32, entry + 6);
  header.writeUInt32LE(png.length, entry + 8); header.writeUInt32LE(offset, entry + 12);
  offset += png.length;
});
await writeFile(path.join(root, 'public/favicon.ico'), Buffer.concat([header, ...pngs]));
console.log('Generated shared SVG, five PNG sizes, maskable app icon and ICO from the same folded-P geometry.');
