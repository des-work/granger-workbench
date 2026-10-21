# Architecture and scope

`pcstudio.easy` handles the short `pc` interface. It classifies explicit requests, gathers context for health/design/source/screen questions, and delegates conversation to an independently installed Hermes Agent. `pcstudio.cli` contains lower-level audio, vision, mesh, and file commands. Ollama handles direct structured planning and image requests.

`pcstudio.jobs` accepts defined build kinds, validates bounds, persists status, launches local builders, and checks expected artifacts. The output is an editable primitive blockout or a supported motion template. It is not a general-purpose CAD system, photogrammetry engine, or unconstrained autonomous programmer.

`pcstudio.research` retrieves actual article passages through the included Kiwix bridge. It can also call a separately installed curated textbook-index adapter. Search snippets do not count as fetched article evidence. Ambiguous topics should trigger clarification. These controls reduce some failure modes; they cannot guarantee a model will reason correctly or cite perfectly.

`integrations/design_assets.py` provides compact metadata from Ultra-PC's local profiles, layouts, fonts, effects, and art. Export builds files into an explicit empty destination. `integrations/device_health.py` reads local machine state. `integrations/hermes_kb.py` confines article requests to its loopback Kiwix endpoint and registered archives.

`ultrapc` is the larger utility library. Its generated design vault is supplied alongside canonical asset generators. Bundled third-party dependencies have a version/hash/license inventory in `assets-vault/dependencies.lock.json`. The historical Ultra-PC command reference describes a broad collection of utilities; availability varies by installed dependency and operating system.

## Boundaries

- The repository contains source and reusable design assets, not private documents, installed model weights, recordings, biometric voice profiles, or live telemetry.
- Optional Termstage and textbook-index integrations refer to external code. The separate full NetMC/Nodesy/Labyrinth projects are not part of this release. `pcstudio.netmc` is a self-contained simple cascade simulation used by this interface.
- Screen observations are requested snapshots with a retained image, not live desktop control. OCR and image-model interpretations can be inaccurate.
- Speaker matching and spoken confirmation are convenience features. Ambient speech, transcription errors, and model behavior remain reasons to constrain tools using the host agent's permission settings.
- The workbench has no claim of zero network traffic. Installation, model downloads, and any enabled Hermes or model provider can use the network. Local inference requires configuring those backends accordingly.
- Linux is the development target. The full interactive workflow has not been validated on Windows, macOS, or arbitrary CPU/GPU configurations.

## Validation approach

Offline checks exercise request routing, ambiguous research handling, job completion/failure reporting, screen-context behavior with mocked models, simulation invariants, and asset integrity. A model response mocked in a test is not a measured AI-quality result. Hardware/audio, external MCP-client interoperability, actual model quality, and deployment permissions require live testing in the intended environment.
