# Repo Plugin Strategy

This repository does not enable any repo-local Cursor plugins by default.

Use repo-local plugins only when a repeated, repo-specific workflow clearly
needs plugin-level behavior that `.cursor/*` guidance cannot cover cleanly.

Current policy:

- Keep `.agents/plugins/marketplace.json` empty until a plugin is ready to be
  intentionally activated.
- Treat `plugins/cognite-sdk-python-starter/` as an inert skeleton, not an
  installed plugin.
- Do not add plugin-local skills, hooks, apps, or MCP servers until the
  workflow is concrete and recurring.
- Prefer repo guidance, shared MCP config, and Bugbot guidance before moving
  behavior into a plugin.
