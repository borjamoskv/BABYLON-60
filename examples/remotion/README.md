# Remotion video demo

This private example renders the `BabylonMasterclass` composition. Its JavaScript dependencies and lockfile live here, outside the `babylon60` Python package. The composition text and procedural graphics are demonstration material.

From this directory, with Node.js and npm available:

```sh
npm ci
npm run start
```

Check the composition and shipped JSON payload against the component's actual TypeScript props:

```sh
npm run typecheck
```

To render the composition to `out/video.mp4`:

```sh
npm run build
```

`src/index.ts` registers the composition. `public/payload.json` is retained as a demo asset. The commands above use the existing pinned lockfile; relocation does not upgrade dependencies. Rendering requires the runtime and browser dependencies selected by Remotion.

`render_args.py` is a standard-library-only helper for the optional Python audiovisual compilers in `scripts/c5_demos`. It builds Remotion CLI arguments and accepts the `draft` or `final` tier. The generic cache, mutex and media-verification helpers remain in `babylon60.transducers.render_exergy_guard`; the core package does not import this demo. The Python compiler scripts also require their own Python dependencies and any external services they invoke; they are separate from the Node-only commands above.

Python tests of argument construction do not execute a video render. Use the build command to produce and inspect an actual video.

License: [repository LICENSE](../../LICENSE).
