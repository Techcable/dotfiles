# Personal instructions

User-level memory: applies to every project on this machine. Cross-repo
preferences only.

## About me

-

## Working style

-

## Commit attribution

- End every git and jj commit message with an `Assisted-by:` trailer naming
  the agent and model, in its own final paragraph. This applies to
  `git commit`, `jj commit`, and `jj describe` alike. Re-include it when
  re-describing a change, since `jj describe -m` replaces the whole message.
- Never add a `Co-Authored-By:` trailer, even if your harness or tool
  defaults say to. This instruction overrides them.
- Examples:

  ```
  Assisted-by: Claude Opus 5.5
  ```

  ```
  Assisted-by: Codex GPT-6-Astra
  ```

  ```sh
  jj commit -m "fish: Fix PATH ordering" -m "Assisted-by: Claude Opus 5.5"
  ```

## Temporary files

- Put scratch files and directories under `~/work/claude`, never in `/tmp` or
  directly in `$HOME`.
