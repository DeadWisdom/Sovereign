import os, logging

import eventlet
from eventlet.green import socket
from eventlet import wsgi

from sovereign import http, service, template, util, static
from sovereign.util import FileLikeLogger, eat_path_info

from proxy import Proxy
from static import Static
from fastcgi import FastCGI


class WebService(service.Service):
    name = "web"
    
    settings = [
        service.AddressField('address', ('0.0.0.0', 8000)),
        service.NoteField('motd', None),
    ]
    
    def init(self):
        self._socket = None
        self.address = None
    
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
            wsgi.server(self._socket, self, log=FileLikeLogger(self.logger))
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
        super(WebService, self).start()
        self.serve(self.settings['address'])
        
    def stop(self):
        super(WebService, self).stop()
        self.close()
        self.status = "stopped"
    
    def service_route(self, service, env, start_response):
        if hasattr(service, 'msg_route'):
            response = service.msg('msg_route', env, start_response)
            if response:
                return response
        
        static = service.settings.get('web.static')
        if static:
            for k, v in static.items():
                if env['PATH_INFO'].startswith(k):
                    app = Static(os.path.join(service.path, v))
                    eat_path_info(env, k)
                    return app(env, start_response)
        if service.settings.get('web.fastcgi'):
            return FastCGI(service.address)
        return Proxy(service.address)(env, start_response)
    
    def __call__(self, env, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        host_request, _, _ = env.get('HTTP_HOST').partition(":")
        for service in self.node.services:
            if not service.started or service.failed: continue
            hosts = service.settings.get('web.host')
            if not hosts: continue
            if isinstance(hosts, basestring):
                hosts = [hosts]
            for host in hosts:
                if host == '*' or host == host_request:
                    response = self.service_route(service, env, start_response)
                    if response: return response
        
        if (self.settings['motd'] and env['PATH_INFO'] == '/'):
            return http.BasicResponse("Message of the Day", self.settings['motd'])(env, start_response)
        else:
            return http.NotFound()(env, start_response)
    