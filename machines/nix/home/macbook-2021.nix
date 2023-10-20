{ pkgs, machineName, system, ... }: {
  home.packages = with pkgs; [
    # GNU Octave (Matlab)
    #
    # We want the 'full' package for QT support.
    # Unfortunately, this package isn't in the Nix cache right now :(
    #
    # For my Math 412 class (Fall 2023), I started using this with Jupyter notebooks
    # I use this with jupyterlab installed via `pipx`
    # Using the PyPi package 'octave_kernel' I add support via `pipx inject`
    #
    # Unfortunately https://github.com/tweag/jupyenv doesn't work with macs yet
    # It also doesn't offer an octave kernel :(
    octaveFull

    #
    # compilers
    #

    # WebAssembly binary toolkit
    wabt

    # lightweight c compiler
    tinycc
  ];
}
