import { describe, expect, it } from "vitest";
import { normalizeBgMask, normalizeBgPixels } from "./localBgRemove";

describe("U²-Net-P preprocessing", () => {
    it("normalizes RGB by the image maximum and emits planar channels", () => {
        const result = normalizeBgPixels(new Uint8ClampedArray([100, 50, 0, 255, 0, 100, 50, 0]));
        expect([...result]).toEqual([expect.closeTo((1-.485)/.229), expect.closeTo(-.485/.229), expect.closeTo((.5-.456)/.224), expect.closeTo((1-.456)/.224), expect.closeTo(-.406/.225), expect.closeTo((.5-.406)/.225)]);
    });
    it("keeps black images finite and normalizes mask range", () => {
        expect([...normalizeBgPixels(new Uint8ClampedArray(8))].every(Number.isFinite)).toBe(true);
        expect([...normalizeBgMask([.2, .4, .6])]).toEqual([0, 128, 255]);
    });
    it("handles constant masks without NaN and rejects invalid model values", () => {
        expect([...normalizeBgMask([0, 0])]).toEqual([0, 0]);
        expect([...normalizeBgMask([1, 1])]).toEqual([255, 255]);
        expect(() => normalizeBgMask([NaN, .5])).toThrow(/invalid mask/);
    });
});
