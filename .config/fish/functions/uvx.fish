# Slightly more secure wrapper of uvx
# , forbidding building from source in interactive mode or running unexpected packages
function uvx --wraps uvx
    if status is-interactive
        # default options
        if not set -q UVX_NO_BUILD
            # by default, pass --no-build to uvx
            set -x UVX_NO_BUILD 1
        end
        # by default, forbid passing packages which match uv subcommand names
        set -la forbidden_packages run init add remove version sync lock help
        set -la forbidden_packages export tree tool python pip venv build
        set -la forbidden_packages publish cache self generate-shell-completions
        set -l target_pkg $argv[1]
        if contains -- "$target_pkg" $forbidden_packages
            echo "$(set_color --bold red)ERROR$(set_color normal):" Execution of target package `$target_pkg` with `uvx` is disabled >&2;
            echo "$(set_color --bold)NOTE$(set_color normal):" Avoid this by passing options or using `uv tool run` >&2;
            return 1;
        end
    end
    set -fx UV_NO_BUILD $UVX_NO_BUILD
    command uvx $argv; or begin
        set -l uvx_status $status
        if test -n "$UV_NO_BUILD"; and status is-interactive;
            echo "$(set_color --bold yellow)WARNING$(set_color normal): The UVX_NO_BUILD environment variable appears to be set" >&2;
        end
        return $uvx_status
    end;
end
