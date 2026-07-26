# Stop homebrew's vendor_conf.d from activating mise mid-startup; config.fish activates it last instead.
set -gx MISE_FISH_AUTO_ACTIVATE 0
