function nix-attrlist
    # using  builtins.attrNames evaluates only the spine of the attrset (which keys exist), never the values bound to them.
    nix eval $argv[1] --json --apply builtins.attrNames $argv[2..]
end
