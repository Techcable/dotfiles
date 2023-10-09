{ pkgs, machineName, system, homeArgs, ... }: let
    username = homeArgs.username or "nicholas";
  in {
  # Latest stable version as of 2023-10-08
  home.stateVersion = "22.05";

  home.username = username;
  home.homeDirectory = {
    aarch64-darwin = /Users;
  }.${system} + /${username};

  # Have home manager install & manage itself
  programs.home-manager.enable = true;
}
