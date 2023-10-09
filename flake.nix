{
  description = "dotfiles & home-manager configuration for Techcable";

  inputs = {
    # Want unstable packages (unless using a server)
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, home-manager, ... }:
    let
      setupMachineHome = { machineName, system, ... } @ homeArgs: home-manager.lib.homeManagerConfiguration (rec {
        # Inherit pkgs from (unstable) nixpkgs
        pkgs = nixpkgs.legacyPackages.${system};
        # These are NixOS modules used to configure home manager
        #
        # See here: https://nix-community.github.io/home-manager/release-notes.html#sec-release-22.11-highlights
        modules = [
          ./machines/nix/home/common.nix
          ./machines/nix/home/${machineName}.nix
        ];

        extraSpecialArgs = {
          inherit system machineName homeArgs;
        };
      });
    in {
      homeConfigurations.macbook-2021 = setupMachineHome {
        machineName = "macbook-2021";
        system = "aarch64-darwin";
      };
    };
}
