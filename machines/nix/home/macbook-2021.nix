{ pkgs, machineName, system, ... }: {

  programs.direnv = {
    enable = true;
    # makes nix usage faster https://github.com/nix-community/nix-direnv
    nix-direnv.enable = true;
  };

  home.packages = with pkgs; [
    ## Misc
    pkgs.devenv

    ## LLMs / AI

    # needed for codex
    mgrep

    ## Cross-Compilation

    # compilers & bintools for x86_64-unknown-linux-musl, appropriately prefixed
    pkgs.pkgsCross.musl64.stdenv.cc
    # Likewise for x86_86-unknown-linux-gnu
    pkgs.pkgsCross.gnu64.stdenv.cc
  ];
}
