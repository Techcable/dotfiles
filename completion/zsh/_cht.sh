#compdef cht.sh

if ! find ~/.cache/cheat.sh -mtime -1d | grep -q list.txt; then 
    mkdir -p ~/.cache/cheat.sh
    curl -s https://cheat.sh/:list -o ~/.cache/cheat.sh/list.txt
fi

__CHTSH_LANGS=($(cat ~/.cache/cheat.sh/list.txt))
_arguments -C \
  '--help[show this help message and exit]: :->noargs' \
  '--shell[enter shell repl]: :->noargs' \
  '1:Cheat Sheet:->lang' \
  '*::: :->noargs' && return 0

if [[ CURRENT -ge 1 ]]; then
    case $state in
        noargs)
             _message "nothing to complete";;
        lang)
             compadd -X "Cheat Sheets" ${__CHTSH_LANGS[@]};;
        *)
             _message "Unknown state, error in autocomplete";;
    esac

    return
fi
