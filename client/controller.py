import socket
import json
import asyncio
import curses
import curses.textpad
from view import GameView
from threading import Thread
import time

# Add to path
import os
import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from networking import packet

# Remove from path
try:
    sys.path.remove(str(parent))
except ValueError:
    pass

class Game():
    def __init__(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
            self.s.connect(('127.0.0.1', 8123))
            self.log: List[str] = []
            self.view = GameView(self)

            p: packet.Packet = packet.receive(self.s)
            if isinstance(p, packet.WelcomePacket):
                self.login()

    def login(self):
        username: str = input("Username: ")
        loginPacket: packet.Packet = packet.LoginPacket(username, "josh")
        packet.send(loginPacket, self.s)

        p = packet.receive(self.s)
        if isinstance(p, packet.OkPacket):
            Thread(target=self.update, daemon=True).start()
            curses.wrapper(self.view.start)
        elif isinstance(p, packet.DenyPacket):
            print(f"Didn't get in. Reason: {p.payloads[0].value}.")
            self.login()

    def update(self):
        while True:
            p: packet.Packet = packet.receive(self.s)
            if isinstance(p, packet.ChatPacket):
                self.log.append(p.payloads[0].value)
                self.log = self.log[max((len(self.log) - 18), 0): ]

    def chat(self):       
        key = self.view.stdscr.getch()
        if key in (curses.KEY_ENTER, curses.ascii.LF, curses.ascii.CR):
            curses.curs_set(True)
            self.view.chatbox = curses.textpad.Textbox(self.view.chatwin)
            message: str = self.view.chatbox.edit()
            self.view.chatbox = None
            self.view.chatwin.clear()
            curses.curs_set(False)
            if message.strip() != '':
                packet.send(packet.ChatPacket(message), self.s)
