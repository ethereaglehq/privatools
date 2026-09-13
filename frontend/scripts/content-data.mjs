import ts from 'typescript';
import { readFileSync } from 'node:fs';

// Read literal content without executing application code. Regex parsing can
// mistake braces, escaped quotes and code examples for record boundaries.
export function parseContentArray(source, variable, ignoredKeys = []) {
  const file = ts.createSourceFile('content.ts', source, ts.ScriptTarget.Latest, true);
  const ignored = new Set(ignoredKeys);
  function literal(node) {
    if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
    if (ts.isNumericLiteral(node)) return Number(node.text);
    if (node.kind === ts.SyntaxKind.TrueKeyword) return true;
    if (node.kind === ts.SyntaxKind.FalseKeyword) return false;
    if (node.kind === ts.SyntaxKind.NullKeyword) return null;
    if (ts.isAsExpression(node) || ts.isSatisfiesExpression(node) || ts.isParenthesizedExpression(node)) return literal(node.expression);
    if (ts.isArrayLiteralExpression(node)) return node.elements.map(literal);
    if (ts.isObjectLiteralExpression(node)) return Object.fromEntries(node.properties.flatMap(property => {
      if (!ts.isPropertyAssignment(property)) throw new Error(`Use literal properties in ${variable}`);
      const key = property.name.text;
      return ignored.has(key) ? [] : [[key, literal(property.initializer)]];
    }));
    throw new Error(`Non-literal content in ${variable}: ${node.getText(file).slice(0, 80)}`);
  }
  for (const statement of file.statements) {
    if (!ts.isVariableStatement(statement)) continue;
    for (const declaration of statement.declarationList.declarations) {
      if (declaration.name.getText(file) !== variable || !declaration.initializer) continue;
      const records = literal(declaration.initializer);
      if (!Array.isArray(records)) throw new Error(`${variable} must be an array`);
      const slugs = new Set();
      for (const record of records) {
        if (!record.slug || slugs.has(record.slug)) throw new Error(`Missing or duplicate slug in ${variable}: ${record.slug}`);
        slugs.add(record.slug);
      }
      return records;
    }
  }
  throw new Error(`Missing content array ${variable}`);
}

export const readContentArray = (path, variable, ignoredKeys) => parseContentArray(readFileSync(path, 'utf8'), variable, ignoredKeys);
