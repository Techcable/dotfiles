# ~/.config/zsh/local.zsh on a node — untracked, NOT managed by home-manager.
# Sourced by programs.zsh.envExtra (nix/homes/users/nicholas/default.nix), which
# lands in the ZDOTDIR .zshenv: the only rc a non-interactive `ssh host '<cmd>'`
# reads. Edits here survive deploys (home-manager never rewrites files it does
# not own) and never reach the ix repo.

# Snapshot the current jj workspace after each non-interactive command that
# arrives over ssh, so remote edits land in jj history. The EXIT trap runs in
# the command's final $PWD, so it captures whatever workspace the command ended
# in (no cd-parsing). `jj util snapshot` is a no-op outside a jj repo and when
# the working copy is clean; errors are swallowed so a shell exit never fails.
if [[ ! -o interactive && -n $SSH_CONNECTION && -z ${_JJ_SNAP_ARMED:-} ]]; then
  export _JJ_SNAP_ARMED=1                       # arm once; nested `zsh -c` skip
  case ${ZSH_EXECUTION_STRING:-} in
    rsync*|scp*|*sftp-server*) ;;               # skip pure transfers
    *) trap 'jj util snapshot >/dev/null 2>&1 || true' EXIT ;;
  esac
fi
