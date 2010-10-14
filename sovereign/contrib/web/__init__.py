import os, logging

import eventlet
from eventlet.green import socket
from eventlet import wsgi

from sovereign import http, service, template, util, static
from sovereign.util import FileLikeLogger

from proxy import proxy


class Service(service.Service):
    settings = service.Service.settings + [
        service.Setting('address', ('0.0.0.0', 8000), tuple),
        service.Setting('motd', None, str),
    ]
    
    def init(self):
        self._thread = None
        self._socket = None
        self._routes = {}
        self.address = None
        
        self.status = "starting"
    
    def serve(self, address):
        """
        Serves the webserver at *address* (host, port).
        """
        if self._socket:
            self.close()
        
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind(tuple(address))
            self._socket.listen(500)
        
            self.address = self._socket.getsockname()
        
            print "Webserver listening on http://%s:%s" % self.address
            self.status = "ready"
            wsgi.server(self._socket, self, log=FileLikeLogger())
            self._socket = None
        except Exception:
            self.status = "failed"
            self.failed = True
            logging.exception("Error serving to address: %r" % (address,))
        finally:
            self.close()
            self.started = False
    
    def close(self):
        if self._socket:
            try:
                self._socket.close()
            except:
                logging.exception("Socket will not shutdown.")
        self._socket = None
        self.address = None
    
    def start(self):
        super(Service, self).start()
        self.serve(self.settings['address'])
        
    def stop(self):
        super(Service, self).stop()
        if (self._thread):
            self._thread.kill()
            self._thread = None
        self.close()
        self.status = "stopped"
    
    def __call__(self, env, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        for app in self.get_routed_apps(env):
            response = app(env, start_response)
            if response: break
        else:
            if (self.settings['motd'] and env['PATH_INFO'] == '/'):
                response = http.BasicResponse("Message of the Day", self.settings['motd'])(env, start_response)
            else:
                response = http.NotFound()(env, start_response)
        return response
    
    def get_routed_apps(self, env):
        hostname, _, _ = env.get('HTTP_HOST').partition(":")
        return tuple(self._routes.get(hostname, ())) + tuple(self._routes.get('*', ()))
    
    def set_route(self, host, app):
        self._routes.setdefault(host, []).append(app)
    
    def proxy_msg(self, host='*', address=None):
        self.set_route(host, proxy(address))