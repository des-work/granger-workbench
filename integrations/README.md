# Local MCP integrations

These are stdio entry points. They do not expose a network MCP service.

| Entry point | Tools / role |
| --- | --- |
| `python -m pcstudio.mcp` | Capability inspection, research, bounded builds/jobs, graph analysis, and simulation |
| `python integrations/hermes_kb.py` | `kb_search`, `kb_read`: actual passages from registered local Kiwix archives |
| `python integrations/design_assets.py` | `design_assets`: compact vault metadata; `design_export`: requested local export |
| `python integrations/device_health.py` | `device_health`: read local machine state |

See [setup](../docs/SETUP.md) for configuration examples and dependencies, and [permissions](../docs/DATA-AND-PERMISSIONS.md) for what these processes can access.

## Kiwix evidence

`kb_search` retrieves search hits plus an actual passage for the first hit. If article fetching fails, it reports an error rather than presenting a search preview as an article. `kb_read` retrieves a selected registered article or a longer passage. Served content IDs use dated ZIM filename stems.

The bridge reads `library.xml` and available ZIM files from `ULTRA_KIWIX_ROOT`. With no override it expects a mounted vault at `/mnt/ultravault`; an explicit root may be an ordinary directory. It starts `kiwix-serve` only on loopback `127.0.0.1:4386` when needed, blocks external content, and rejects redirects outside that endpoint. ZIM archives and their licenses are supplied by the user.

```bash
export ULTRA_KIWIX_ROOT="/absolute/path/your-zim-library"
python integrations/hermes_kb.py --check
python integrations/verify_live.py
```

The optional `verify_live.py --hermes --model your-installed-model` check additionally runs an installed Hermes assistant, inspects that run's tool evidence, and verifies citation/no-results behavior. It creates local diagnostic output and can take minutes. It is a live integration check, not part of the offline test suite.

Previous workstation-specific verification notes and service overrides are not part of this release's setup instructions. No claim is made that a new machine already has its models, archive library, or host-agent routing configured.
