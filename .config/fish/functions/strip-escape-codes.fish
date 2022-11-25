function strip-escape-codes --description "Strips ANSI escape codes from stdin";
    #argparse --max-args=0 'h/help' -- $argv or return;

    if set --query _flag_help
        echo "USAGE: strip-escape-codes [opts..]" >&2;
        echo "" >&2;
        echo "Strips ANSI ecapse codes from std input." >&2;
    end
    # NOTE: When building this regex, \\d appeared cursed :/
    sed -E "s/\\$(echo -en '\e')\[([[:digit:]]+;)*([[:digit:]]+m)//g";
end
