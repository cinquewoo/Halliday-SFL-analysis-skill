# Project instructions

## Halliday SFL plugin update order

For every change to `plugins/halliday-sfl-analysis-skill`:

1. Update the canonical local plugin source first.
2. Run the Plugin Creator cachebuster helper after the content is final.
3. Validate the Skill, plugin manifest, bundled scripts, and relevant regression cases.
4. Reinstall `halliday-sfl-analysis-skill@halliday-sfl` from the local marketplace and verify the installed version with `codex plugin list`.
5. Tell the user to start a new Codex task because an existing task does not hot-reload updated skills.
6. Only after local installation and validation succeed, commit, push, open or merge the pull request, and publish any requested GitHub release.

Do not publish the Halliday plugin to GitHub before the local chat plugin has been updated and verified unless the user explicitly overrides this order.

Preserve private source files, local corpus indexes, absolute source mappings, and unrelated uncommitted work. Never upload copyrighted source documents merely to distribute the plugin.
