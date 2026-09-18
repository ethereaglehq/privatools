import type { env as TransformersEnv } from "@huggingface/transformers";

/**
 * Settings every on-device transformers.js model on this site shares. Call it
 * on the `env` of the dynamically imported module before the first pipeline.
 *
 * Models always come from the Hugging Face hub (never from this site's origin)
 * and are cached by transformers.js in the browser Cache API.
 *
 * transformers.js v4 also stores the ONNX Runtime WASM files in that same
 * cache by default (`useWasmCache`). The AI hub lists and deletes models by
 * reading that cache (lib/localModels.ts), so runtime files it does not
 * recognise would take tens of megabytes the hub neither shows nor clears.
 * Keep the runtime in the browser's HTTP cache, as v3 did.
 */
export function configureTransformers(env: typeof TransformersEnv): void {
    env.allowLocalModels = false;
    env.allowRemoteModels = true;
    env.useWasmCache = false;
}
