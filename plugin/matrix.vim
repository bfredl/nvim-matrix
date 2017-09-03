nnoremap <Plug>(Matrix-Send) :call MatrixSend(getline('.'))<cr>
nnoremap <Plug>(Matrix-Me) :call MatrixMe(getline('.'))<cr>

func! _matrix_cr()
    " TODO: multiline mode, check <c-x> mode etc
    return "\<c-o>:call MatrixSend(getline('.'))\<cr>\<c-o>dd"
endfunc
