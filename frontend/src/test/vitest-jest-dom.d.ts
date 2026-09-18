// jest-dom 7 still declares its matchers on Vitest's one-parameter `Assertion<T>`.
// Vitest 5 changed that interface to `Assertion<R, T>`, and TypeScript merges
// only declarations with identical type parameters, so it drops jest-dom's and
// every matcher (toBeInTheDocument, toHaveTextContent, …) vanishes from the
// types. The runtime is unaffected: setup.ts still registers the matchers with
// expect.extend. Vitest's `Assertion` extends `Matchers<R, T>`, so declaring
// them there restores them. Delete this file once jest-dom ships Vitest 5 types:
// https://github.com/testing-library/jest-dom/issues/738
import type { TestingLibraryMatchers } from "@testing-library/jest-dom/matchers";

declare module "vitest" {
  interface Matchers<R, T> extends TestingLibraryMatchers<unknown, R> {}
}
