function scp-anyhost --wraps scp --description "scp wrapper that disables host-key checking";
    # NOTE: See also `ssh-anyhost`
    echo "$(set_color --bold yellow)WARNING:$(set_color normal) Disabling ssh host-key checking";
    scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $argv
end
