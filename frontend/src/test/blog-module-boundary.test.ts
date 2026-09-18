import { existsSync, readFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import ts from "typescript";
import { describe, expect, it } from "vitest";

// data/blog.ts is every article's HTML. Only blog routes may load it, through a
// dynamic import(). A static import from any module below puts it on every
// page that module reaches: main.tsx's graph is the shell every visitor runs,
// and withRealTools mounts ToolPage/NonPdfToolPage (for ToolUI) on every tool
// page. scripts/check-bundle-size.mjs guards the built entry and preloads;
// this also covers the lazily mounted tool modules, which no preload lists.
const src = join(process.cwd(), "src");
const blog = join(src, "data/blog.ts");
const roots = ["main.tsx", "pages/ToolPage.tsx", "pages/NonPdfToolPage.tsx"];

function resolveModule(from: string, specifier: string): string | undefined {
    const base = specifier.startsWith("@/") ? join(src, specifier.slice(2)) : specifier.startsWith(".") ? resolve(dirname(from), specifier) : undefined;
    if (!base) return undefined; // a package
    return [base, `${base}.ts`, `${base}.tsx`, join(base, "index.ts"), join(base, "index.tsx")].find(path => /\.tsx?$/.test(path) && existsSync(path));
}

/** Imports that survive compilation: `import type` and all-type specifier lists are erased. */
function valueImports(file: string): string[] {
    const source = ts.createSourceFile(file, readFileSync(file, "utf8"), ts.ScriptTarget.Latest);
    return source.statements.flatMap(statement => {
        if (ts.isImportDeclaration(statement)) {
            const clause = statement.importClause;
            const bindings = clause?.namedBindings;
            const typesOnly = clause?.isTypeOnly || (clause && !clause.name && bindings && ts.isNamedImports(bindings) && bindings.elements.length > 0 && bindings.elements.every(element => element.isTypeOnly));
            return typesOnly ? [] : [(statement.moduleSpecifier as ts.StringLiteral).text];
        }
        if (ts.isExportDeclaration(statement) && statement.moduleSpecifier && !statement.isTypeOnly) return [(statement.moduleSpecifier as ts.StringLiteral).text];
        return [];
    }).map(specifier => resolveModule(file, specifier)).filter((path): path is string => Boolean(path));
}

/** The static import chain from `root` to data/blog.ts, or [] when there is none. */
function chainToBlog(root: string): string[] {
    const parent = new Map<string, string | null>([[root, null]]);
    const queue = [root];
    while (queue.length) {
        const file = queue.shift()!;
        if (file === blog) {
            const chain: string[] = [];
            for (let at: string | null = file; at; at = parent.get(at) ?? null) chain.unshift(relative(src, at));
            return chain;
        }
        for (const next of valueImports(file)) if (!parent.has(next)) { parent.set(next, file); queue.push(next); }
    }
    return [];
}

describe("the blog module stays off every non-blog page", () => {
    it.each(roots)("src/%s does not import data/blog.ts statically", root => {
        expect(chainToBlog(join(src, root)), "static import chain to data/blog.ts").toEqual([]);
    });
});
