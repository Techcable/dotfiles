function biff -d="alias biff=bttf" --wraps bttf
    warning "The `biff` command has been renamed to `bttf`"
    bttf $argv
end
