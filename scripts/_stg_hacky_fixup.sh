#!/usr/bin/env zsh

# Hack to workaround broken GPG signing in `stg refresh`
local previous_count="${GIT_CONFIG_COUNT:-0}"
local new_count="$(( $previous_count + 1 ))"

export GIT_CONFIG_COUNT="$(( previous_count + 1 ))"
export "GIT_CONFIG_KEY_${previous_count}=commit.gpgsign"
export "GIT_CONFIG_VALUE_${previous_count}=false"

exec stg "$@"
