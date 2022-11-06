dotfile config
===============
A simple configuration system for my dotfiles.

**TODO**: Switch to python + strictyaml

Everything here is managed by the `scripts/dotfile-config` program.

Each machine has its own subdirectory in `config/$MACHINE_NAME`.

There are (see below for details)

## "Semi Secrets"
These files contain private information (like personal emails, public keys),
that I would rather not have exposed on Github.

**WARNING**: This is **unencrypted** on the disk!

### Security
It should be kept private, but is not required to be encrypted (so there is no need to be kept 

There are *no passwords/secret keys* that would lead to compromised accounts.

The only protection from publicly revealing any of this information is the .gitignore file.

## Templates
The templates for each config are kept in the "template" directory.

## Misc notes
