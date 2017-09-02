import neovim
from matrix_client.client import MatrixClient
from functools import partial
import re
from collections import deque

class obj:
    pass
self = obj()

class ExclusiveHandler(object):
    """Wrapper for buffering incoming messages from a asynchronous source.

    Wraps an async message handler function and ensures a previous message will
    be completely handled before next messsage is processed. Is used to avoid
    iopub messages being printed out-of-order or even interleaved.
    """
    def __init__(self, handler):
        self.msgs = deque()
        self.handler = handler
        self.is_active = False

    def __call__(self, *args):
        self.msgs.append(args)
        if not self.is_active:
            self.is_active = True
            while self.msgs:
                self.handler(*self.msgs.popleft())
            self.is_active = False

re_gitter = r"@gitter_([^:]+):matrix.org"
re_freenode = r"@freenode_([^:]+):matrix.org"
re_matrix = re.compile(r"@([^:]+):matrix.org")

@neovim.plugin
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
        lineidx = len(self.buf)

        self.buf.append(data.split("\n")) # not splitlines

        for w in self.vim.windows:
            if w.buffer == self.buf and w != self.vim.current.window:
                w.cursor = [len(self.buf), int(1e9)]

        return lineidx

    def format_sender(self, sender):
        m = re_matrix.match(sender)
        if not m:
            return sender, None
        name = m.group(1)

        if name.startswith("gitter_"):
            display = "@"+name[len("gitter_"):]
            return display, "GitterUser"
        if name.startswith("freenode_"):
            display = name[len("freenode_"):]
            return display, "FreenodeUser"
        if name == self.user:
            return name, "SelfUser"
        return name, "MatrixUser"

    def on_message(self, room, event):
        if event['type'] == "m.room.member":
            if event['membership'] == "join":
                self.buf_write("{0} joined".format(event['content']['displayname']))
        elif event['type'] == "m.room.message":
            if event['content']['msgtype'] == "m.text":
                name, hl = self.format_sender(event['sender'])
                line = self.buf_write("{0}: {1}".format(name, event['content']['body']))
                if hl:
                    self.buf.add_highlight(hl, line, 0, len(name))
            elif event['content']['msgtype'] == "m.emote":
                self.buf_write("* {0} {1}".format(event['sender'], event['content']['body']))
            else:
                self.buf_write("X " + event['content']['msgtype'])
        else:
            self.buf_write(event['type'])

    @neovim.command("MatrixConnect", sync=True)
    def matrix_connect(self):
        self.create_outbuf()
        self.client = MatrixClient("https://matrix.org")
        user = self.vim.vars["matrix_user"]
        self.user = user
        pw = self.vim.vars["matrix_passwd"]

        token = self.client.login_with_password(username=user, password=pw)
        self.room = self.client.join_room(self.vim.vars["matrix_room"])

        self.room.add_listener(partial(self.vim.async_call, ExclusiveHandler(self.on_message)))
        self.client.start_listener_thread()
        self.members = self.room.get_joined_members()
        self.room.backfill_previous_messages(limit=50)

    @neovim.function("MatrixSend", sync=True)
    def matrix_send(self, args):
        text, = args
        self.room.send_text(text)

    @neovim.function("MatrixMe", sync=True)
    def matrix_me(self, args):
        text, = args
        self.room.send_emote(text)
