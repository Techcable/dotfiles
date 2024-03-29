
" Configure tabs -> 4 spaces
set tabstop=4
set shiftwidth=4
set expandtab
set smartindent

call plug#begin('~/.vim/plugged')

" WARNING: Plugins are not automatically installed
"
" They must be installed manually with :PlugInstall
"
" Run :PlugStatus to check install status
" Run :PlugUpdate to update plugins

Plug 'bakpakin/janet.vim'
Plug 'NoahTheDuke/vim-just'
Plug 'dag/vim-fish'
Plug 'HiPhish/jinja.vim'

" Asynchronous Lint Engine
" TODO: This is too fancy for me right now
" Plug 'dense-analysis/ale'

" Configure ALE lint engine
let g:ale_linters = {'python': ['black', 'ipython', 'mypy', 'ruff']}

call plug#end()

