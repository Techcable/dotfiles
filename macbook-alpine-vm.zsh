# Configuration for the Alpine Linux VM, running inside my 2021 Macbook Pro ^_^

extend_path ~/.cargo/bin
if [[ -d "$HOME/bin" ]]; then
  # My private bin ($HOME/bin) 
  extend_path ~/bin
fi

# On alpine, sudo -> doas
alias sudo='doas'

# Set default python to python3
alias python='python3'
