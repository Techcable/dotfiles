__all__ = ["configure"]


def configure(repl):
    # With persistent history, there's really
    # no need to confirm exit....
    repl.confirm_exit = False

    # Begin in VI mode (because it's the best)
    repl.vi_mode = True

    # enable mouse support
    repl.enable_mouse_support = True

    # Highlight matching parethesis.
    repl.highlight_matching_parenthesis = True

    # NOTE: Be careful because some colorschemes are hard
    # to see in the terminal!
    repl.use_code_colorscheme("monokai")
    repl.min_brightness = .30
    repl.color_depth = "DEPTH_24_BIT" # Truecolor

    # If output is very large, use a pager
    repl.enable_pager = True
