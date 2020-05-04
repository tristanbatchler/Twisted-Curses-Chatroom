import json
import pickle
import socket
import traceback
from typing import *
from .payload import *


class Packet:
    MAX_LENGTH: int = 2 ** 63 - 1
        
    def __init__(self, *payloads: Payload):
        self.action: str = type(self).__name__
        self.payloads: Tuple[Payload] = payloads

    def tobytes(self) -> str:
        serialize_dict: Dict[str, str] = {}
        serialize_dict['a'] = self.action
        for i in range(len(self.payloads)):
            serialize_dict[f'p{i}'] = self.payloads[i].serialize()
        jsonstr: str = json.dumps(serialize_dict, separators=(',', ':'))
        lengthstr: str = str(len(jsonstr))
        return str.encode(lengthstr + jsonstr, 'utf-8')

    
    def __repr__(self) -> str:
        return f"{self.action}: {self.payloads}"


class OkPacket(Packet):
    pass


class DenyPacket(Packet):
    def __init__(self, reason: str = "unspecified"):
        super().__init__(Payload(reason))


class WelcomePacket(Packet):
    def __init__(self, motd: str = "Welcome to MoonlapseMUD"):
        super().__init__(Payload(motd))


class LoginPacket(Packet):
    def __init__(self, username, password: str):
        pusername = Payload(username)
        ppassword = Payload(password)
        super().__init__(pusername, ppassword)


class ChatPacket(Packet):
    def __init__(self, message: str):
        pmessage: Payload = Payload(message[:80])
        super().__init__(pmessage)


def frombytes(data: bytes) -> Packet:
    """
    Constructs a proper packet type from bytes encoding a utf-8 string formatted like so:
    63{
        "a": "PacketClassName",
        "p0": "A payload", 
        "p1": "Another payload"
    }

    The number at the very beginning and before the first '{' is the length of the rest of the 
    packet in bytes after whitespace has been removed.

    There is no ending semi-colon.

    The payload is automatically pickled and converted to a hex string in order to be sent over 
    the network. This allows you to send and receive all picklable Python objects.
    """
    datastr: str = data.decode('utf-8')
    begin_idx: int = datastr.index('{')
    obj_dict: Dict[str, str] = json.loads(datastr[begin_idx: ])

    action: Optional[str] = None
    payloads: List[Optional[Payload]] = []
    for key in obj_dict:
        value: str = obj_dict[key]
        if key == 'a':
            action = value
        elif key[0] == 'p':
            index: int = int(key[1:])
            payloadbytes = bytes.fromhex(value)
            payloads.insert(index, pickle.loads(payloadbytes))
    
    # Use reflection to construct the specific packet type we're looking for
    specificPacketClassName:str = action
    try:
        constructor: Type = globals()[specificPacketClassName]
        rPacket = constructor(*tuple(payloads))
        return rPacket
    except KeyError:
        print(f"KeyError: {specificPacketClassName} is not a valid packet name. Stacktrace: ")
        print(traceback.format_exc())

def send(p: Packet, s: socket.socket):
    s.sendall(p.tobytes())

def receive(s: socket.socket):
    length: bytes = b''
    json: bytes = b''
    for i in range(len(str(Packet.MAX_LENGTH))):
        c: bytes = s.recv(1)
        if c != b'{':
            try:
                int(c)
            except ValueError:
                break
            length += c
        else:
            data: bytes = b'{' + s.recv(int(length) - 1)
            return frombytes(length + data)

    raise PacketParseError("Error reading packet length. Either too long or contains non-digit characters.")

class PacketParseError(Exception):
    pass
