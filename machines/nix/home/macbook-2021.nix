{ pkgs, machineName, system, ... }: {
  home.packages = with pkgs; [
    ## LLMs / AI

    # needed for codex
    mgrep
  ];
}
