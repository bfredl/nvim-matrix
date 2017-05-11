import neovim
from matrix_client.client import MatrixClient
from functools import partial

class obj:
    pass
self = obj()

@neovim.plugin
@neovim.encoding(True)
class IPythonPlugin(object):
    def __init__(self, vim):
        self.vim = vim
        self.buf = None
        self.client = None

    def create_outbuf(self):
        vim = self.vim
        if self.buf is not None:
            return
        w0 = vim.current.window
        vim.command(":new")
        buf = vim.current.buffer
        buf.options["swapfile"] = False
        buf.options["buftype"] = "nofile"
        buf.name = "[matrix]"
        vim.current.window = w0
        self.buf = buf

    def buf_write(self, data):
        #self.hl_handler.reset_sgr()
        lineidx = len(self.buf)-1
        lastline = self.buf[-1]

        txt = lastline + data
        self.buf[-1:] = txt.split("\n") # not splitlines

        for w in self.vim.windows:
            if w.buffer == self.buf and w != self.vim.current.window:
                w.cursor = [len(self.buf), int(1e9)]

        return lineidx

    def on_message(self, room, event):
        if event['type'] == "m.room.member":
            if event['membership'] == "join":
                self.buf_write("{0} joined".format(event['content']['displayname']))
        elif event['type'] == "m.room.message":
            if event['content']['msgtype'] == "m.text":
                self.buf_write("{0}: {1}".format(event['sender'], event['content']['body'])+"\n")
            elif event['content']['msgtype'] == "m.emote":
                self.buf_write("* {0} {1}".format(event['sender'], event['content']['body'])+"\n")
            else:
                self.buf_write("X " + event['content']['msgtype'])
        else:
            self.buf_write(event['type'])

    @neovim.command("MatrixConnect", sync=True)
    def matrix_connect(self):
        self.create_outbuf()
        self.client = MatrixClient("https://matrix.org")
        user = self.vim.vars["matrix_user"]
        pw = self.vim.vars["matrix_passwd"]

        token = self.client.login_with_password(username=user, password=pw)
        self.room = self.client.join_room(self.vim.vars["matrix_room"])

        self.room.add_listener(partial(self.vim.async_call, self.on_message))
        self.client.start_listener_thread()

    @neovim.function("MatrixSend", sync=True)
    def matrix_send(self, args):
        text, = args
        self.room.send_text(text)

    @neovim.function("MatrixMe", sync=True)
    def matrix_me(self, args):
        text, = args
        self.room.send_emote(text)
