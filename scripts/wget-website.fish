#!/usr/bin/env fish
# Script to download an entire website
argparse --max-args=0 'd/domain=' 'O/output-dir=' -- $argv; or exit;

if not set -q _flag_domain;
    echo "ERROR: Must specify domain" >&2;
    exit 1;
end
if set -q _flag_output_dir
    set output_dir $_flag_output_dr
else
    # default output directory
    set output_dir $HOME/work/websites
end
if not set -q output_dir
    echo "ERROR: Missing output directory `$output_dir`" >&2;
    exit 1;
end


set target_domain $_flag_domain

if not string match --quiet --regex --entire '([\w_-]+)(\.[\w_-]+)+' -- $target_domain;
    echo "\x1b[ERROR: Invalid domain `$target_domain`";
    exit 1;
end

# TODO: Sometimes only downloads a single file?
wget --recursive --page-requisites --convert-links --execute robots=off --html-extension --convert-links --restrict-file-names=windows -U Mozilla "https://$target_domain" --directory-prefix "$HOME/data/websites/$target_domain"
