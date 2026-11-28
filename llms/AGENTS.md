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
- Use the full name of the model used in the session (e.g. `GPT-6-Astra`
  or `GPT-6.1-Sol`). Do not shorten the model name to `GPT-6`.
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

## GitHub issue attribution

- Whenever you file a GitHub issue (via `gh issue create`, the API, or any
  other tool), start the issue body with a GitHub alert saying that AI
  drafted it. Name the agent and full model name, as in commit trailers.
- Pick the wording by whether I reviewed the draft:
  - **Not reviewed** (filed without me reading the final text):

    ```markdown
    > [!WARNING]
    > This issue was drafted automatically by an AI agent (Claude Opus 5.5)
    > and **has not been reviewed by a human**.
    ```

  - **Reviewed** (I read the final text and approved it before filing):

    ```markdown
    > [!NOTE]
    > This issue was drafted by an AI agent (Claude Opus 5.5) and reviewed
    > by a human before filing.
    ```

- If I edit or approve the text after you file it, switch to the reviewed
  `[!NOTE]` version.

## Temporary files

- Put scratch files and directories under `~/work/claude`, never in `/tmp` or
  directly in `$HOME`.
