nnoremap <Plug>(Matrix-Send) :call MatrixSend(getline('.'))<cr>
nnoremap <Plug>(Matrix-Me) :call MatrixMe(getline('.'))<cr>

nnoremap <Plug>(Matrix-SetMe) :call _matrix_setme(1-g:matrix_me)<cr>

hi link MatrixBg MatrixSendBg
let g:matrix_me = 0

func! _matrix_setme(on)
    if a:on
        hi link MatrixBg MatrixMeBg
    else
        hi link MatrixBg MatrixSendBg
    end
    let g:matrix_me = a:on
endfunc

func! _matrix_cr()
    if g:matrix_me
        return "\<c-o>:call MatrixMe(getline('.'))\<cr>\<c-o>:call _matrix_setme(0)\<cr>\<c-o>\"_dd"
    else
        " TODO: multiline mode, check <c-x> mode etc
        return "\<c-o>:call MatrixSend(getline('.'))\<cr>\<c-o>\"_dd"
    end
endfunc
