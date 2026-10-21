# Data and permissions

The default direct model endpoint is loopback Ollama. Conversation is delegated to the user's Hermes installation, whose own provider, browser, and tool settings determine where data goes. Configuring a remote endpoint can send prompts, passages, screenshots, or machine readings to that endpoint. Inspect both configurations before giving the assistant private context.

## Local state

- `output/pcstudio/` contains recordings, screenshots, generated files, reports, and jobs. Some failures can retain partial files; review and remove them yourself when finished.
- `models/` contains separately obtained speech/model files and optional speaker-enrollment state. Voice profiles are biometric data; keep this directory private.
- `~/.local/state/pcstudio/assistant.json` stores assistant preferences. Hermes separately manages its own sessions and logs.
- Ultra-PC creates configuration, indexes, caches, and reports according to its command settings. Keep private source libraries and runtime data outside version control.

These directories and common local configuration files are excluded by this repository's `.gitignore`. An ignore rule does not protect a file already committed in a different repository or manually forced into Git.

## Tool authority

The MCP bridges use stdio and inherit the launching user's filesystem and process permissions. They are not a sandbox. Device health reads machine state. Research reads registered archives and the configured curated index. Design export and build tools write explicitly requested local files; some builders launch Blender or FFmpeg. Hermes may provide additional tools with broader authority, governed by its own configuration.

Review the tool list before enabling a server, use a constrained account/environment for untrusted tasks, and configure the host agent's approval policy for consequential actions. Natural-language confirmation and speaker matching do not replace operating-system permissions.

## Reporting a problem

For an ordinary bug, open a GitHub issue with reproduction steps and sanitized output. Do not attach recordings, screenshots, prompts, machine reports, credentials, or reference documents unless you intend to make them public. For a security issue, use GitHub's private vulnerability-reporting feature if enabled; otherwise request a private contact route without posting the exploit or sensitive data publicly.
