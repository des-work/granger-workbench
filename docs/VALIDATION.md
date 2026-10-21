# Public release validation

The release snapshot was checked on **2026-10-21**, on Linux with Python **3.14.6**. This is one development environment, not a platform-support matrix or an AI-quality benchmark.

| Check | Result |
| --- | --- |
| Pytest suite | 138 passed; 110 additional unittest subtests passed |
| Optional external Termstage composition test | 1 skipped: Termstage is not distributed in this repository |
| Ultra-PC smoke suite, model downloads disabled | 39 passed, 0 failed |
| Design bridge capability check | 27 styles, 46 effects, 15 page packs available |
| Configuration / security regressions | Checkout-relative integration roots, role/endpoint overrides, TLS-default preservation, explicit Kiwix-directory configuration, and external-redirect rejection covered |

Run from the source checkout after installing `requirements-dev.txt`:

```bash
python -m pytest -q --import-mode=importlib tests integrations/tests
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python tests/smoke.py
python integrations/design_assets.py --check
```

Most assistant and renderer tests use mocked model or process responses. Their results establish control flow, input validation, and failure handling, rather than factual answer quality or rendering quality. Full interactive voice, microphone/speaker devices, alternative hardware, external Termstage, Hermes-provider routing, and arbitrary local model behavior were not revalidated for this public snapshot. The default model examples are not weights included in the release.

Vendored assets retain their recorded hashes and upstream license texts. Whitespace in generated art and vendored license files is preserved deliberately.
