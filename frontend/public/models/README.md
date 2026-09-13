# Browser background removal assets

PrivaTools distributes the unchanged **U²-Net-P** ONNX model from Daniel Gatis's rembg release, based on U²-Net by Xuebin Qin and collaborators. Browser preprocessing and compositing are implemented separately by PrivaTools; the weights are not modified. This is the compact general foreground model, not BRIA/RMBG.

- Model: https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx
- SHA-256: `309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8`
- Independently downloaded and matched against the existing local model on September 14, 2026.
- U²-Net source and attribution: https://github.com/xuebinqin/U-2-Net — Apache License 2.0, complete text in `U2NET-LICENSE.txt`.
- rembg distribution: https://github.com/danielgatis/rembg — MIT, Copyright (c) 2020 Daniel Gatis, complete text in `REMBG-LICENSE.txt`.
- ONNX Runtime: https://github.com/microsoft/onnxruntime — MIT, Copyright (c) Microsoft Corporation, complete text in `ONNXRUNTIME-LICENSE.txt`.

`npm run dev` and `npm run build` stage the model plus the installed, lockfile-pinned ONNX Runtime CPU WASM and matching `.mjs` bootstrap here. The generated `asset-manifest.json` records each file's size and hash. Generated binaries are ignored by git and copied into the release's public assets. No browser model input is uploaded by this staging script. It runs during development/build, and fetches the public release only if no valid local model is available.

Use `PRIVATOOLS_U2NETP_PATH` to point at an existing copy in an offline build; a mismatched hash fails the build. A damaged generated copy also fails explicitly so it cannot silently become a shipped model. The browser inference code owns download consent, progress and cache removal.
