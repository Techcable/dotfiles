
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

" Allows easily commenting out lines of text
" See `:help Comment-nvim` for details and keybindings
Plug 'numToStr/Comment.nvim'

" language server
Plug 'neovim/nvim-lspconfig'

" Asynchronous Lint Engine
" TODO: This is too fancy for me right now
" Plug 'dense-analysis/ale'

" Configure ALE lint engine
let g:ale_linters = {'python': ['black', 'ipython', 'mypy', 'ruff']}

call plug#end()

" initalize language servers
lua <<EOF
-- harper-ls - grammar checking
require('lspconfig').harper_ls.setup {
    settings = {
        ["harper-ls"] = {
            -- consistent dictionary file across systems
            userDictPath = "~/.config/harper-ls/dictionary.txt",
            -- in markdown files we want these as warnings
            diagnosticSeverity = "warning",
        }
    }
}
require('lspconfig').typos_lsp.setup {}
vim.lsp.enable('harper_ls')
-- restrict harper to prose files
vim.lsp.config['harper_ls'].filetypes = { 'markdown', 'gitcommit', }
EOF

" setup Comment.vim default keybindings
"
" TODO: How to invoke this functionality via a command?
" I don't want to use keybindings
lua require('Comment').setup()
