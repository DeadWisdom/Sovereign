#!../env/bin/python

import tradesocket, eventlet, os, atexit, sys
from eventlet.greenio import trampoline
from eventlet.green import socket

eventlet.import_patched('multiprocessing.process')
multiprocessing = eventlet.import_patched('multiprocessing')


class BaronRequest(object):
    def __init__(self, type, data):
        self.type = type
        self.data = data

    def __unicode__(self):
        return "%s %r" % (self.type, self.data)
        
    def __repr__(self):
        return "%s %r" % (self.type, self.data)

class BaronServer(object):
    def __init__(self, childpid, pipe, unix_socket):
        self._childpid = childpid
        self._pipe = pipe
        self._unix_socket = unix_socket
        self._sockets = set()
        self.loop()
    
    def loop(self):
        while 1:
            try:
                request = self._pipe.recv()
            except EOFError:
                pid, code = os.waitpid(self._childpid)
                sys.exit(code)
            self.handle_request(request)
    
    def handle_request(self, request):
        if request.type == 'socket':
            sock = self.create_socket(**request.data)
            status = tradesocket.send_fd( self._unix_socket.fileno(), sock.fileno())
            if (status < 0):
                raise RuntimeError("Send error, status: %r" % status)
            self._pipe.send(True)
            self.close_socket(sock)
        elif request.type == 'exit':
            self._pipe.send(True)
            sys.exit(request.data.get('code', 0))
        else:
            raise RuntimeError("Invalid Baron request: %r" % request)
    
    def create_socket(self, address=('', 0), reusable=True, listen=500):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if reusable:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(address)
        sock.listen(listen)
        self._sockets.add(sock)  # We have to store it, or else it gets 
                                 # closed when it goes out of scope.
        return sock

    def close_socket(self, sock):
        self._sockets.remove(sock)
        sock.close()

class Baron(object):
    def __init__(self):
        server_pipe, client_pipe = multiprocessing.Pipe()
        server_unix_sock, client_unix_sock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        
        if server_unix_sock.family != socket.AF_UNIX:
            raise ValueError("Only AF_UNIX sockets are allowed")
            
        pid = os.fork()
        if pid == 0:
            server_pipe.close()
            server_unix_sock.close()
            self._pipe = client_pipe
            self._unix_socket = client_unix_sock
        else:
            client_pipe.close()
            client_unix_sock.close()
            BaronServer(pid, server_pipe, server_unix_sock)
            sys.exit(0)     # If we get here, somehow, die.
    
    def create_socket(self, address):
        self.send('socket', address=address)
        fd = tradesocket.recv_fd(self._unix_socket.fileno())
        if (fd == -1):
            raise RuntimeError("Error in recv_fd(), message length is negative.")
        if (fd == -2):
            raise RuntimeError("Error in recv_fd(), cmessage is null.")
        if (fd == -3):
            raise RuntimeError("Error in recv_fd(), cmessage is il-formed.")
        return socket.fromfd( fd, socket.AF_INET, socket.SOCK_STREAM )

    def exit(self, code=0):
        return self.send('exit', code=code)
    
    def send(self, typ, **data):
        request = BaronRequest(typ, data)
        self._pipe.send(request)
        try:
            response = self._pipe.recv()
        except EOFError:
            response = None
        return response

def make_socket(address=('', 0), reusable=True, listen=500):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if reusable:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(listen)
    return sock

if __name__ == '__main__':
    # Quick test
    baron = Baron()
    sock = baron.create_socket(('0.0.0.0', 5000))
    print sock.getsockname()
    sock = baron.create_socket(('0.0.0.0', 5001))
    print sock.getsockname()
    baron.exit()