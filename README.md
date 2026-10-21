# Granger Workbench

**A local AI workbench for asking questions, inspecting a workstation, and turning explicit requests into verifiable local work.**

Granger Workbench brings together three parts of an ongoing personal research and engineering project:

| Component | Role |
| --- | --- |
| **PC Ask** (`pc ask`) | Typed or spoken requests, evidence gathering, and interaction with an installed Hermes assistant. |
| **Granger** (`pc granger`) | The voice interface: wake-word standby, spoken conversation, and optional speaker matching. |
| **Ultra-PC** (`ultra.py`) | The underlying toolkit: diagnostics, offline references, retrieval, media utilities, and a reusable design asset vault. |

The repository was previously named **Ultra-PC**. The existing command and package names remain available.

## What it does

- Retrieves passages from a user-provided Kiwix library; an optional external textbook-index adapter supports curated sources.
- Gives the assistant actual device readings, local design metadata, and explicitly requested screenshots as context.
- Starts bounded 3D blockout or animation jobs and checks their output files before reporting completion.
- Exposes research, graph analysis, simulation, design lookup/export, and device health through local MCP stdio servers.
- Provides local CLI tools for graph analysis, Monte Carlo demonstrations, media conversion, troubleshooting, and design scaffolding.

This is a **working prototype developed on Linux**, rather than a finished cross-platform assistant. Some commands are useful by themselves; voice, vision, and assistant-driven work require the optional software described below. Screenshot capture currently targets COSMIC. Terminal artwork generation requires a separate Termstage installation. The bundled `pcstudio.netmc` is a small cascade simulator, not the separate full NetMC research suite.

## Start with the tools that need no AI service

Requires Python 3.10+; Linux is the supported development platform. Use a source checkout so the bundled design assets remain next to the code.

```bash
git clone https://github.com/des-work/granger-workbench.git
cd granger-workbench
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-pcstudio.txt

python ultra.py --help
python -m pcstudio.easy sim dice --dice 2 --target 7 --op == --trials 20000
python integrations/design_assets.py --check
python integrations/device_health.py --check
```

For the short commands, add this checkout's `bin` directory to your PATH:

```bash
export PATH="$PWD/bin:$PATH"
pc --help
pc capabilities
```

`pc capabilities` probes your installed services and dependencies. An unavailable feature is expected until its prerequisites are configured.

## Add the assistant

Install and configure [Ollama](https://ollama.com/) and [Hermes Agent](https://github.com/NousResearch/hermes-agent) separately. Select a chat model installed in your own inference setup; configure Hermes to use that backend. The model names below are examples, not included weights or tested hardware requirements.

```bash
export PCSTUDIO_CHAT_MODEL="your-installed-chat-model"
export PCSTUDIO_BUILD_MODEL="your-installed-planning-model"
export PCSTUDIO_VISION_MODEL="your-installed-vision-model"
pc ask --text "What can this workstation actually do?" --no-play
```

Install the optional speech requirements and a Piper voice before using `pc ask` with the microphone or `pc granger`. See [setup and feature requirements](docs/SETUP.md) for CPU/GPU differences, audio tools, model downloads, and MCP configuration.

## How it is put together

```text
Typed request / microphone
          |
     PC Ask / Granger
          |
    Request-specific context
    health | sources | design | screen
          |
   Configured Hermes / local models
          |
    Tool request or bounded build
          |
     Verified result / explicit failure
```

Research text and screenshots are treated as untrusted context. The interface distinguishes a queued job from a completed artifact. Language-model answers can still be wrong; neither speaker matching nor natural-language confirmation is a security boundary.

## Documentation

- [Setup and optional dependencies](docs/SETUP.md)
- [Architecture, scope, and limitations](docs/ARCHITECTURE.md)
- [Release validation and limits](docs/VALIDATION.md)
- [Data handling and tool permissions](docs/DATA-AND-PERMISSIONS.md)
- [Ultra-PC command reference](docs/ULTRA-PC-REFERENCE.md)
- [MCP integration entry points](integrations/README.md)
- [Design vault](assets-vault/DESIGN-SYSTEM.md)
- [Third-party assets and licenses](THIRD_PARTY_NOTICES.md)

## Validation

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q --import-mode=importlib tests integrations/tests
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python tests/smoke.py
```

These checks cover routing, validation, failure handling, source evidence, job bookkeeping, asset integrity, and CLI behavior. They do **not** establish model accuracy, microphone reliability on other machines, or the quality of arbitrary generated designs. Live hardware and model behavior require separate testing.

## Project status

Built by Desmond Workman as part of a broader interest in local AI infrastructure, cybersecurity architecture, and usable technical tools. Development uses frontier-model coding assistance alongside local testing and manual review, and prioritizes reliable local interfaces, explicit dependencies, and honest reporting of what a tool actually accomplished. Contributions that improve reproducibility, Linux portability, and evidence handling are welcome.

Original project code is provided under the [MIT License](LICENSE). Bundled fonts and libraries retain their own licenses. Models, voices, reference archives, personal configuration, recordings, and speaker profiles are not included.
