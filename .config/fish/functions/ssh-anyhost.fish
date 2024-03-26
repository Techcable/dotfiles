function ssh-anyhost --wraps ssh --description "ssh wrapper that disables host-key checking";
    echo "$(set_color --bold yellow)WARNING:$(set_color normal) Disabling ssh host-key checking";
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $argv
end
