"""
The sovereign child process webserver.  This file will be moved into the
service path if it isn't already provided.

Elements were taken from Spawning by Donovan Preston.
"""
import os, sys

from eventlet import tpool, wsgi, patcher
from eventlet.green import socket
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import AdminMediaHandler


def serve():
    config = get_config()
    socket = config['socket']
    threads = config['threads']
    
    app = WSGIHandler()
    app = AdminMediaHandler(app)
    
    if (threads > 0):
        app = tpool_wsgi(app)
    else:
        patcher.monkey_patch(all=False, socket=True)
    
    wsgi.server(socket, app, log=StdOutLogger())


def resolve_app(sig):
    """
    Resolves the app function based on an import string:
    
    >>> resolve_app('wsgi.resolve_app') == resolve_app
    True
    """
    if sig is None:
        raise RuntimeError("No app has been specified.")
    if callable(sig):
        return sig
    module, app = sig.rsplit('.', 1)
    m = __import__(module, fromlist=[app])
    return getattr(m, app)


def get_config():
    option = lambda k, d: os.environ.get(k, d)
    config = {
        'app': option('SOVEREIGN_APP', None),
        'threads': int(option('SOVEREIGN_THREADS', 0)),
        'host': option('SOVEREIGN_HOST', '*'),
        'port': int(option('SOVEREIGN_PORT', 0)),
        'socket': int(option('SOVEREIGN_SOCKET', None)),
        'virtual_env': option('SOVEREIGN_VIRTUAL_ENV', None),
    }
    
    if config['socket']:
        config['socket'] = socket.fromfd( config['socket'], socket.AF_INET, socket.SOCK_STREAM )
    
    if not config['socket']:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((config['host'], config['port']))
        sock.listen(500)
        config['socket'] = sock
        
    if config['virtual_env']:
        activate_this = os.path.join( config['virtual_env'], 'bin', 'activate_this.py' )
        execfile(activate_this, dict(__file__=activate_this))
    
    return config 


def tpool_wsgi(app):
    def tpooled_application(e, s):
        result = tpool.execute(app, e, s)
        # return builtins directly
        if isinstance(result, (basestring, list, tuple)):
            return result
        else:
            # iterators might execute code when iterating over them,
            # so we wrap them in a Proxy object so every call to
            # next() goes through tpool
            return tpool.Proxy(result)
    return tpooled_application


class StdOutLogger(object):
    def write(self, out):
        print out.strip()
        sys.stdout.flush()


if __name__ == '__main__':
    serve()