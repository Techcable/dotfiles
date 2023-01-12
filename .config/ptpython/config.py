__all__ = ["configure"]


def configure(repl):
    # default to vi mode
    repl.vi_mode = True

    # enable mouse support
    repl.enable_mouse_support = True

    # Highlight matching parethesis.
    repl.highlight_matching_parenthesis = True

    # NOTE: Be careful because some colorschemes are hard
    # to see in the terminal!
    repl.use_code_colorscheme("monokai")

    # If output is very large, use a pager
    repl.enable_pager = True
