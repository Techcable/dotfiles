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

    # alternate pagers
    moar
    ov

    #
    # compilers & interpreters
    #

    # WebAssembly binary toolkit
    wabt

    # janet
    janet
    jpm # janet package manager

    # LaTeX configuration
    #
    # I use Nix for Tex Live packages to avoid need for either
    # the MacTex installer or the homebrew cask.
    # Even better, I avoid needing the "Tex Live" update utility.
    #
    # See here:
    # - https://nixos.wiki/wiki/TexLive
    # - https://nixos.org/manual/nixpkgs/stable/#sec-language-texlive
    (texlive.combine {
        # A tex 'scheme' is a collection of packages. This is an upstream TeX Live concept that
        # Nix has adopted. Some of the options include scheme-small, scheme-medium, scheme-full
        #
        # Here we choose 'scheme-tetex', which according to the
        # nixos.wiki is "more then medium scheme, but nowhere near the full scheme"
        #
        # As of this writing (2023-11-19), it downloads about 1 or 2 GiB of content.
        inherit (pkgs.texlive) scheme-tetex;
    })
  ];
}
