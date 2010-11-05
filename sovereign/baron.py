import eventlet, os, sys, passfd
from eventlet.green import socket

eventlet.import_patched('multiprocessing.process')
multiprocessing = eventlet.import_patched('multiprocessing')

class BaronRequest(object):
    def __init__(self, type, **data):
        self.type = type
        self.data = data

    def __unicode__(self):
        return "~%s %r" % (self.type, self.data)
        
    def __repr__(self):
        return "~%s %r" % (self.type, self.data)


class BaronServer(object):
    def __init__(self, sock):
        self.client = sock
    
    def loop(self):
        while 1:
            try:
                request = self.client.recv()
            except EOFError:
                sys.exit(0)
            
            print "Request received:", request
            if request.type == 'socket':
                passfd.sendfd( self.client, self.create_socket(**request.data) )
            elif request.type == 'exit':
                sys.exit(request.data.get('code', 0))
            else:
                raise RuntimeError("Invalid Baron request type: %r" % request.type)
            
        sys.exit(0)
    
    def create_socket(self, address=('', 0), reusable=True, listen=500):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if reusable:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(address)
        sock.listen(listen)
        return sock.fileno()


class BaronClient(object):
    def __init__(self, socket):
        self.server = socket
    
    def create_socket(self, address):
        self.server.send(BaronRequest('socket', address=address))
        fd = passfd.recvfd(self.server)
        return socket.fromfd( fd, socket.AF_INET, socket.SOCK_STREAM )

    def exit(self, code=0):
        self.server.send(BaronRequest('exit', code=code))


def create_baron():
    server, client = multiprocessing.Pipe()
    pid = os.fork()
    if pid == 0:
        server = BaronServer(client)
        server.loop()
    else:
        return BaronClient(server)


if __name__ == '__main__':
    # Quick test
    client = create_baron()
    sock = client.create_socket(('0.0.0.0', 8008))
    client.exit()