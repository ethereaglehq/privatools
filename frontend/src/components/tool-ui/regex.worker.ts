/** Disposable worker keeps pathological expressions away from the UI thread. */
self.onmessage = (event: MessageEvent<{pattern:string; flags:string; text:string}>) => {
    try {
        const {pattern, flags, text} = event.data, expression = new RegExp(pattern, flags);
        const matches: {match:string; index:number; groups:(string | undefined)[]}[] = [];
        if (flags.includes("g")) { for (const match of text.matchAll(expression)) { matches.push({match:match[0],index:match.index ?? 0,groups:match.slice(1)}); if (matches.length >= 1000) break; } }
        else { const match = expression.exec(text); if (match) matches.push({match:match[0],index:match.index,groups:match.slice(1)}); }
        self.postMessage({kind:"ok",matches,truncated:matches.length >= 1000});
    } catch (error) { self.postMessage({kind:"err",error:error instanceof Error ? error.message : "Invalid expression."}); }
};
export {};
