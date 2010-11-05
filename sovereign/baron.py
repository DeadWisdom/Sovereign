import tradesocket, eventlet, os, atexit, sys, grp, pwd, signal
from setproctitle import setproctitle, getproctitle
from eventlet.greenio import trampoline
from eventlet.green import socket
from signal import SIGTERM

eventlet.import_patched('multiprocessing.process')
multiprocessing = eventlet.import_patched('multiprocessing')

### Utilities ###
def create_socket(address=('', 0), reusable=True, listen=500):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if reusable:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(listen)
    return sock

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
        
        atexit.register(self.die)
        signal.signal(signal.SIGTERM, self.die)
        
        self.loop()
    
    def die(self, sig, func=None):
        os.kill(self._childpid, SIGTERM)
        try:
            self._pipe.close()
            self._unix_socket.close()
        except:
            pass
        os._exit(0)
    
    def loop(self):
        while 1:
            try:
                request = self._pipe.recv()
            except EOFError:
                print "Baron lost its child."
                pid, code = os.waitpid(self._childpid, 0)
                sys.exit(code)
            except KeyboardInterrupt:
                sys.exit(0)
            attr = "handle_" + request.type
            if hasattr(self, attr):
                getattr(self, attr)(**request.data)
            else:
                raise RuntimeError("Invalid Baron request: %r" % request)
    
    def handle_socket(self, **args):
        sock = create_socket(**args)
        status = tradesocket.send_fd( self._unix_socket.fileno(), sock.fileno())
        if (status < 0):
            raise RuntimeError("Send error, status: %r" % status)
        self._pipe.send(True)
        sock.close()    # We don't need this anymore, discard.
    
    def handle_exit(self, returncode=0):
        self._pipe.send(True)
        sys.exit(returncode)

class Baron(object):
    def __init__(self):
        self._pipe = None
    
    def fork(self):
        if (self._pipe): #We've already forked.
             return
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
            setproctitle("%s #baron" % getproctitle())
            BaronServer(pid, server_pipe, server_unix_sock)
            sys.exit(0)     # If we get here, somehow, die.
    
    def get_owner_spec(self, spec):
        user, _, group = spec.partition(":")
        if group:
            group = grp.getgrnam(group)
        else:
            try:
                group = grp.getgrnam(user)
            except:
                group = None
        if user:
            user = pwd.getpwnam(user)
        else:
            user = None
        return user, group
    
    def set_owner(self, spec):
        user, group = self.get_owner_spec(spec)
        if user:
            print "Changing to user: %s" % user.pw_name
            os.setuid(user.pw_uid)
        if group:
            print "Changing to group: %s" % group.gr_name
            os.setgid(group.gr_id)
        return user, group
    
    #def daemonize(self, working_dir, umask, stdout='/tmp/stdout', stdin=os.devnull, stderr='/tmp/stderr'):
    def daemonize(self, working_dir, umask, stdout=os.devnull, stdin=os.devnull, stderr=None):
        """Fork the process into the background."""
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            msg = "fork #1 failed: (%d) %s\n" % (e.errno, e.strerror)
            sys.stderr.write(msg)
            sys.exit(1)

        working_dir = os.path.abspath(working_dir)

        os.chdir('/')
        os.umask(umask)
        os.setsid()

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            msg = "fork #2 failed: (%d) %s\n" % (e.errno, e.strerror)
            sys.stderr.write(msg)
            sys.exit(1)

        if stderr is None:
            stderr = stdout

        si = file(stdin, 'r')
        so = file(stdout, 'a+')
        se = file(stderr, 'a+', 0)

        pid = str(os.getpid())

        sys.stderr.write("deamon started (%s)\n"  % pid)
        sys.stderr.flush()

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
        os.chdir(working_dir)
        
        return pid
    
    def ensure_pid_path(self, pid_file, userspec=None):
        if userspec:
            user, group = self.get_owner_spec(userspec)
            if user:
                user = user.pw_uid
            else:
                user = -1
            if group:
                group = group.gr_id
            else:
                group = -1
        else:
            user, group = -1, -1
        
        full = os.path.abspath(os.path.dirname(pid_file))
        make = []
        while not os.path.exists(full):
            full, tail = os.path.split(full)
            make.insert(0, tail)
        
        for part in make:
            full = os.path.join(full, part)
            os.mkdir(full)
            os.chown(full, user, group)
    
    def start_daemon(self, pid_file, working_dir='.', umask=0):
        pid_file = os.path.abspath(pid_file)
        
        pf = None
        try:
            pf = file(pid_file, 'r')
            pid = int(pf.read().strip())
        except IOError:
            pid = None
        finally:
            if pf:
                pf.close()
        
        if pid:
            sys.stderr.write("Cannot daemonize, pid file '%s' exists.\n" % pid_file)
            sys.stderr.write("If you are sure the process (%d) isn't " \
                             "running, try --restart.\n" % pid)
            sys.exit(1)
        
        pid = self.daemonize(working_dir, umask)
        
        try:
            pf = file(pid_file, 'w+')
            pf.write("%s\n" % pid)
        except IOError:
            raise
            sys.stderr.write("Could not write to the pid file: %s\n" % pid_file)
            sys.exit(1)
        finally:
            if pf:
                pf.close()
    
    def stop_daemon(self, pid_file):
        pf = None
        try:
            pf = file(pid_file, 'r')
            pid = int(pf.read().strip())
        except IOError:
            pid = None
        finally:
            if pf:
                pf.close()
        
        if not pid:     # No pidfile, means we're stopped, logically.
            return
        
        try:
            while 1:
                os.kill(pid, SIGTERM)
                eventlet.sleep(1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                os.remove(pid_file)
            else:
                raise
    
    def send(self, typ, **data):
        request = BaronRequest(typ, data)
        self._pipe.send(request)
        try:
            return self._pipe.recv()
        except EOFError:
            return None

    def create_socket(self, address=('', 0), reusable=True, listen=500):
        if (self._pipe):
            self.send('socket', address=address, reusable=reusable, listen=listen)
            fd = tradesocket.recv_fd(self._unix_socket.fileno())
            if (fd < 0):
                raise RuntimeError("Error in tradesocket.recv_fd()")
            return socket.fromfd( fd, socket.AF_INET, socket.SOCK_STREAM )
        else:
            return create_socket(address)

    def exit(self, code=0):
        return self.send('exit', code=code)
    

if __name__ == '__main__':
    # Quick test
    baron = Baron()
    sock = baron.create_socket(('0.0.0.0', 5000))
    print sock.getsockname()
    sock = baron.create_socket(('0.0.0.0', 5001))
    print sock.getsockname()
    baron.exit()