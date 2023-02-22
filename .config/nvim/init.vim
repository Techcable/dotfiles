
" Configure tabs -> 4 spaces
set tabstop=4
set shiftwidth=4
set expandtab
set smartindent

call plug#begin('~/.vim/plugged')

Plug 'bakpakin/janet.vim'
Plug 'NoahTheDuke/vim-just'
Plug 'dag/vim-fish'

" Asynchronous Lint Engine
Plug 'dense-analysis/ale'

call plug#end()

