from twisted.protocols.basic import IntNStringReceiver
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from networking import packet
from typing import *


class Moonlapse(IntNStringReceiver):
    def __init__(self, users: Dict[str, 'Moonlapse']):
        self.users: Dict[str, 'Moonlapse'] = users
        self.username: str = None
        self.state: function = self._GETLOGIN

    def connectionMade(self):
        self.sendPacket(packet.WelcomePacket())

    def connectionLost(self, reason="unspecified"):
        if self.username in self.users:
            del self.users[self.username]
            for name, protocol in self.users.items():
                if protocol != self:
                    protocol.sendPacket(packet.ChatPacket(f"{self.username} has departed..."))

    def dataReceived(self, data: bytes) -> None:
        p: packet.Packet = packet.frombytes(data)
        print(f"Received packet {p}")
        if isinstance(p, packet.LoginPacket) and self.state == self._GETLOGIN:
            self._GETLOGIN(p)
        elif isinstance(p, packet.ChatPacket) and self.state == self._CHAT:
            self._CHAT(p)

    def _GETLOGIN(self, p: packet.LoginPacket):
        username: str = p.payloads[0].value
        if username in self.users.keys():
            self.sendPacket(packet.DenyPacket("username already taken"))
            return
        self.sendPacket(packet.OkPacket())
        self.username = username
        self.users[username] = self

        for name, protocol in self.users.items():
            protocol.sendPacket(packet.ChatPacket(f"{self.username} has arrived!"))

        self.state = self._CHAT

    def _CHAT(self, p: packet.ChatPacket):
        message: str = f"{self.username} says: {p.payloads[0].value}"
        if message.strip() != '':
            for name, protocol in self.users.items():
                protocol.sendPacket(packet.ChatPacket(message))


    def sendPacket(self, p: packet.Packet):
        self.transport.write(p.tobytes())
        print(f"Sent packet {p}")


class MoonlapseFactory(Factory):
    def __init__(self):
        self.users: Dict[str, 'Moonlapse'] = {}

    def buildProtocol(self, addr):
        return Moonlapse(self.users)


if __name__ == '__main__':
    reactor.listenTCP(8123, MoonlapseFactory())
    reactor.run()
