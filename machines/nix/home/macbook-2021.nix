{ pkgs, machineName, system, ... }: {
  home.packages = with pkgs; [
    # GNU Octave (Matlab)
    #
    # We want the 'full' package for QT support.
    # Unfortunately, it isn't in the cache right now :(
    octaveFull

    # Scientific computing
    jupyter-all
  ];
}
