# If the `xsv` CSV toolkit is missing,
# gives a descriptive error to use the `xan` tool instead.
#
# If both are installed and we are in an interactive session,
# still give a warning suggesting use of `xan`
#
# The xsv command is unfortunately unmaintained:
# <https://github.com/burntSushi/xsv>
#
# The `xan` command is a fork which has many more features:
# <https://github.com/medialab/xan>
# Unfortunately, it is not guarenteed to be fully compatible

begin
    set --local funcdef_args
    if command -q xsv
        set --append funcdef_args
        function xsv $funcdef_args --wraps xsv --description='alias xsv=warning "..."; xsv'
           if status is-interactive
               echo $(set_color --bold yellow)WARNING$(set_color normal): The `xsv` toolkit is deprecated, use `xan` instead >&2;
            end
            command xsv $argv
        end
    else
        function xsv --description="missing command, use xan instead"
            echo $(set_color --bold red)ERROR$(set_color normal): The `xsv` toolkit is not installed. Use `xan` as a modern alternative. >&2
            return 1
        end
    end
end
