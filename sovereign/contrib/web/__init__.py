import os, logging

import eventlet
from eventlet.green import socket
from eventlet import wsgi

from sovereign import http, service, template, util, static
from sovereign.util import FileLikeLogger, eat_path_info

from proxy import Proxy
from static import Static
from fastcgi import FastCGI


class Service(service.Service):
    name = "web"
    
    settings = [
        service.AddressField('address', ('0.0.0.0', 80)),
        service.NoteField('motd', None),
    ]
    
    def serve(self):
        """
        Serves the webserver at *address* (host, port).
        """
        self._socket = self.node.build_socket(self.settings['address'])
        self.address = self._socket.getsockname()
        try:
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
                self._socket.terminate()
            except:
                logging.exception("Socket will not shutdown.")
        self.address = None
    
    def start(self):
        super(Service, self).start()
        self.serve()
        
    def stop(self):
        super(Service, self).stop()
        self.close()
        self.status = "stopped"
    
    def service_route(self, service, env, start_response):
        if hasattr(service, 'route_msg'):
            self.logger.debug("Routing to service: %s", service.id)
            response = service.msg('route', environ=env, start_response=start_response)
            if response is not None:
                return response
            else:
                self.logger.debug("Service failed to give a response: %r", service.id)
        
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
        host_request, _, _ = env.get('HTTP_HOST', '').partition(":")
        for service in self.node.services:
            if not service.started or service.failed: continue
            hosts = service.settings.get('web.host')
            if not hosts: continue
            if isinstance(hosts, basestring):
                hosts = [hosts]
            for host in hosts:
                if host == '*' or host == host_request:
                    response = self.service_route(service, env, start_response)
                    if response is not None: return response
        
        if (self.settings['motd'] and env['PATH_INFO'] == '/'):
            return http.BasicResponse("Message of the Day", self.settings['motd'])(env, start_response)
        else:
            return http.NotFound()(env, start_response)
    