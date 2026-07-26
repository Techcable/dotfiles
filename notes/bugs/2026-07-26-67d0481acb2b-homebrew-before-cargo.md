# Why `/opt/homebrew/bin` moved relative to `~/.cargo/bin` (mise PATH reordering)

Date: 2026-07-26
Trigger commit: 67d0481acb2b / jj change `xlxkpxqwlvrz` — "fish: Move homebrew init to conf.d"
Compared revisions: master (`zqkpkvku`, 25cb8b15936d) vs `qouyqvotmm` (dfc6fc1cdc32)

> **TL;DR / lesson: `mise activate` must always be the LAST thing in shell
> startup.** Its design assumes the PATH is fully built when it activates;
> anything added to PATH after activation gets reshuffled by its prompt
> hook. Homebrew's vendor conf.d snippet activates mise in the *middle* of
> fish startup, which is the entire bug.

## Symptom

In a new kitty shell:

- On **master**: `/opt/homebrew/bin` sits early in `$PATH` (~#9), while
  `~/.cargo/bin` and the other `fish_add_path --append` dirs (dotfiles
  scripts, JetBrains, go, Coursier, senpai, macports, janet, …) sit at the
  **tail** (~#30+).
- On **qouyqvotmm** (before the homebrew-to-conf.d move): `/opt/homebrew/bin`
  instead landed *behind* the cargo block, near the end.

Nothing in the diff between the two revisions obviously touches this
ordering — the homebrew init code is identical, it just moved from
`config.fish` to `conf.d/00-homebrew.fish`.

## Root cause: mise rewrites `$PATH` after fish config finishes

The PATH observed in an interactive shell is **not** the PATH fish's config
produces. Three phases matter:

1. **Startup order.** Fish sources conf.d snippets before `config.fish`, and
   Homebrew's vendor snippet `vendor_conf.d/mise-activate.fish` runs *after*
   the user's `conf.d/*.fish` but *before* `config.fish`. At that moment
   `mise activate fish` snapshots the current PATH into `__MISE_ORIG_PATH`.
   The snapshot therefore contains whatever the user conf.d added (nix,
   python, and — on master — homebrew via `00-homebrew.fish`) plus the
   system/`path_helper` dirs, but **none** of the additions made later by
   `config.fish` → `machines/shellrc/common.fish` → `macbook_2021.fish`
   (cargo, opam, `~/bin`, scripts, JetBrains, …).

2. **Fish's own ordering.** The rest of the config runs and
   `fish_add_path --global` entries get hoisted to the front of `$PATH` by
   fish's `__fish_reconstruct_path` handler (it re-prepends the whole
   `$fish_user_paths` block on every change). At the end of startup the PATH
   genuinely has `~/.cargo/bin` around #7 and `/opt/homebrew/bin` around #21
   — verified with a full pty simulation of a kitty window (clean env,
   interactive login fish).

3. **The mise prompt hook reorders everything.** At the first prompt,
   `__mise_env_eval` runs `mise hook-env -s fish | source`, which reconciles
   the current PATH against the `__MISE_ORIG_PATH` snapshot:
   - entries prepended *before* the snapshot's first entry stay in front
     (opam, `~/.local/bin`, `~/bin`);
   - the snapshot itself becomes the stable backbone, in order;
   - every other entry added after the snapshot (the whole cargo/scripts/
     JetBrains/… block) is **relegated to the tail**, after the backbone.

   Proof: feeding `mise hook-env` the fish-built PATH plus the inherited
   `__MISE_ORIG_PATH` reproduces the observed shell PATH entry-for-entry,
   and the `__MISE_DIFF` blob it emits is byte-identical to the one found in
   the live session environment.

## mise's PATH model (why activation order is a hard requirement)

mise models PATH as three segments:

```
[ user prepends ]  [ mise-managed tool dirs ]  [ __MISE_ORIG_PATH backbone ]
```

`__MISE_DIFF`/`__MISE_SESSION` record which entries mise itself added, so
`hook-env` can subtract them and re-add per-directory tool dirs
idempotently. `__MISE_ORIG_PATH` is the anchor marking where the "world at
activation time" begins. Interactive prepends made *in front of* the
backbone (venv activation, ad-hoc `fish_add_path`) are classified as user
changes and preserved. But mise has **no bucket for new entries scattered
inside its backbone** — and that is exactly what the rest of fish startup
produces, because `__fish_reconstruct_path` interleaves `fish_user_paths`
entries among backbone entries. Everything hook-env can't classify as a
leading prepend gets swept to the tail.

This is why mise's docs say to put `mise activate` at the *end* of the
shell config: the invariant only holds if the snapshot equals the final,
fully-built PATH. Activating mid-startup (as Homebrew's vendor snippet
does) is not a slightly-degraded mode — it feeds the model a PATH that is
still under construction, and every later addition is silently reordered.

## Why the trigger commit flipped the order

The commit didn't change what homebrew init does — it moved it across
**mise's snapshot boundary**:

- **master**: `00-homebrew.fish` runs before `mise-activate.fish`, so
  `/opt/homebrew/bin` is *inside* `__MISE_ORIG_PATH`. mise keeps it in the
  backbone (~#9), ahead of the relegated cargo block.
- **qouyqvotmm**: homebrew init lived in `config.fish`, which runs *after*
  the snapshot. mise treated `/opt/homebrew/bin` as a late addition and
  pushed it to the tail, behind cargo.

The same boundary effect explains why `/opt/homebrew/opt/mise/bin` swapped
sides with `/opt/homebrew/bin` between the revisions.

## Red herrings ruled out

- The fish config itself produces the *same* cargo-before-homebrew order on
  both revisions (tested: fresh `env -i` login shells, nested shells, and
  pty-interactive shells against exact snapshots of each revision's
  `.config/fish`).
- Non-interactive shells (`fish -c`, scripts) never show a prompt, so the
  mise hook never fires — they see fish's ordering, not mise's. This is why
  naive reproduction attempts disagree with real terminal windows.
- kitty's own environment is clean (`PATH=/usr/bin:/bin:/usr/sbin:/sbin`,
  Dock launch; checked via `ps eww` on the kitty process) — no inherited
  PATH baggage is involved.

## Fix

**Rule: `mise activate` always comes last.** Disable Homebrew's vendor
auto-activation and activate at the very bottom of `config.fish`, after
every PATH modification (including machine shellrc):

```fish
# in any user conf.d file (user conf.d runs before vendor_conf.d):
set -gx MISE_FISH_AUTO_ACTIVATE 0

# LAST lines of config.fish — nothing may touch $PATH after this:
if command -q mise
    mise activate fish | source
end
```

Then the snapshot includes everything, `hook-env` has nothing to
rearrange, and fish's own ordering (`fish_user_paths` block first) is what
interactive shells actually get. Any future PATH additions must be added
*above* the activation line — treat that as an invariant of config.fish.

Alternative if the prompt-hook cost is ever unwanted: shims mode
(`fish_add_path --global ~/.local/share/mise/shims`, no activation), at
the cost of `mise.toml` env vars not auto-loading and `command -v`
resolving to shims.

Caveat when rolling out: long-running kitty windows (and processes spawned
from them) still carry stale `__MISE_ORIG_PATH`/`__MISE_DIFF`/
`__MISE_SESSION`; open fresh windows to see the fix take effect.
