# encoding: utf-8

from cos.routines.socket                        import FileReadWait, FileWriteWait


__all__ = ['Socket']



class Socket(object):
    def __init__(self, sock):
        self.sock = sock
    
    def accept(self):
        yield FileReadWait(self.sock)
        client, addr = self.sock.accept()
        yield Socket(client), addr
    
    def send(self, buffer):
        while buffer:
            yield FileWriteWait(self.sock)
            length = self.sock.send(buffer)
            buffer = buffer[length:]
    
    def receive(self, length):
        yield FileReadWait(self.sock)
        yield self.sock.recv(length)
    
    recv = receive # Compatability with raw socket API.  Abbreviations suck.
    
    def close(self):
        yield self.sock.close()
