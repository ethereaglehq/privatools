import { expect, it } from "vitest";
import { modelProgress } from "./modelProgress";
import { transcriptTime, transcriptSrt } from "./speechTranscript";
it("keeps multiple model-file downloads monotonic and reserves 100 for ready", () => {
    const values: number[] = []; const report = modelProgress(value => values.push(value), 1100);
    report({status:'progress', file:'config', loaded:100, total:100});
    report({status:'progress', file:'model', loaded:10, total:1000});
    report({status:'done', file:'model'});
    expect(values).toEqual([9,10,99]); report({status:'ready'}); expect(values).toEqual([9,10,99,100]);
});
it("carries rounded subtitle milliseconds into the next second and minute", () => {
    expect(transcriptTime(59.9996)).toBe('00:01:00,000');
    expect(transcriptTime(3599.9996)).toBe('01:00:00,000');
    expect(transcriptTime(-1)).toBe('00:00:00,000');
    expect(transcriptSrt([{start:0,end:1.9996,text:' Hello '}])).toBe('1\n00:00:00,000 --> 00:00:02,000\nHello\n');
});
