try:
    import json
except:
    import simpljson as json

import os, sys, logging, platform

import eventlet
from eventlet import wsgi
from eventlet.green import socket
from eventlet.greenpool import GreenPool

from sovereign import http
from sovereign.util import FileLikeLogger, shell
from sovereign.service import get_service_class, ServiceIdCollision
from sovereign.dispatcher import Dispatcher
from sovereign.deployment import Deployment

from base import Node


class LocalNode(Node):
    def __init__(self, path=None, id=None, master=None, settings=None):
        self.path = os.path.abspath(path or '.')
        
        if id is None:
            id = platform.node()
        
        self.id = id
        
        if not os.path.exists(self.path):
            os.makedirs(path)
        
        print "Sovereign node (%s) created at %s" % (self.id, self.path)
        
        self.address = None
        self._socket = None
        
        self.services = []
        self._service_map = {}
        self._deployments = []
        
        self._node_map = {id: self}
        self.master = master or self
        self.neighbors = []     # Any node we know about.
        self.vassals = []
        self.rogue = []         # TODO: Put nodes that should be vassals 
                                # but don't recognize us here.
                                
        self._pool = GreenPool()
        
        if (self.master != self):
            self._node_map[self.master.id] = self.master
        
        self.dispatcher = Dispatcher(self)
        
        self.load_settings(settings=settings)
    
    def serve(self, address=("127.0.0.1", 1648)):
        """
            Serves the rest client at *address*.
        """
        if self._socket:
            self.close()
        
        self.start()
        
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind(tuple(address))
            self._socket.listen(500)
        
            self.address = self._socket.getsockname()
        
            print "listening on http://%s:%s" % self.address
            wsgi.server(self._socket, self, log=FileLikeLogger())
            self._socket = None
        except Exception:
            logging.exception("Error binding address.")
        finally:
            self.close()
            
    def spawn_thread(self, func, *args, **kwargs):
        thread = self._pool.spawn(func, *args, **kwargs)
        eventlet.sleep(0)
        return thread
    
    def start(self):
        for service in self.services:
            if not service.started and not service.disabled:
                service.start()
        
    def stop(self):
        for service in self.services:
            if service.started:
                service.stop()
    
    def close(self):
        if self._socket:
            try:
                self._socket.close()
            except:
                logging.exception("Socket will not shutdown.")
                pass
        self._socket = None
        self.address = None
    
    def __call__(self, env, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        response = self.route(env)
        if (response is None):
            response = http.NotFound()
        return response(env, start_response)
    
    def route(self, env):
        for service in self.services:
            response = service.route(env)
            if response is not None:
                return response
        
        return self.dispatcher.route(env)
    
    def load_settings(self, settings=None):
        path = os.path.join(self.path, 'settings.json')
        if settings is False or (not os.path.exists(path) and not settings):
            settings = {
                'services': [{
                    'id': 'admin',
                    'type': 'sovereign.contrib.admin.Service',
                }]
            }
        elif not settings:
            settings = json.load(open(path, 'r'))
        
        for service in settings.get('services', ()):
            self.create_service(service['id'], service)
    
    def save_settings(self):
        path = os.path.join(self.path, 'settings.json')
        json.dump(self.info(), open(path, 'w'))
    
    ### Implementations ###
    def sys_install(self, packages):
        from system import sys_install
        return sys_install(packages)
    
    def sys_upgrade(self, packages):
        from system import sys_upgrade
        return sys_upgrade(packages)
        
    def sys_uninsall(self, packages):
        from system import sys_uninsall
        return sys_uninsall(packages)
    
    def pip_install(self, packages, env=None):
        if (env):
            cmd = "pip -E %s install %%s" % env
        else:
            cmd = "pip install %s"
        
        return self.sys(cmd % p for p in packages)
    
    def pip_uninstall(self, packages, env=None):
        if (env):
            cmd = "pip -E %s uninstall %%s" % env
        else:
            cmd = "pip uninstall %s"
        
        return self.sys(cmd % p for p in packages)
    
    def sys(self, cmds):
        stdout = []
        stderr = []
        for cmd in cmds:
            o, e = shell(self.path, cmd)
            stdout.append(o)
            stderr.append(e)
        return stdout, stderr
    
    def info(self):
        info = {
            'id': self.id,
            'address': self.address,
            'services': [service.info() for service in self.services],
            'vassals': [node.info() for node in self.vassals]
        }
        if self.master is not self:
            info['master'] = self.master.address
        return info
    
    def create_service(self, id, settings):
        if self._get_service(id):
            raise ServiceIdCollision("Cannot create another service with the same id: %r" % id)
        
        ServiceCls = get_service_class(settings['type'])
        service = ServiceCls(node=self, id=id, settings=settings)
        self.services.append(service)
        self._service_map[id] = service
        
        if not service.settings.get('disabled', False):
            service.deploy()
        self.save_settings()
        return service.info()
        
    def modify_service(self, id, settings):
        self.delete_service(id)
        return self.create_service(id, settings)
    
    def delete_service(self, id):
        service = self._get_service(id)
        if (not service):
            return True
        service.delete()
        self.services.remove(service)
        self._service_map.pop(id)
        self.save_settings()
        return True
    
    def msg_service(self, id, message, **kwargs):
        service = self._get_service(id)
        return service.msg(message, **kwargs)
    
    def get_service(self, id):
        service = self._get_service(id)
        if (service):
            return service.info()
        return None
    
    def _get_service(self, id):
        return self._service_map.get(id, None)
    
    def create_local_node(self, id=None, path=None, settings=None):
        if self.get_node(id):
            raise NodeIdCollision("Cannot create a node with the id of another, known node: %r" % id)
        
        settings['type'] = 'local'
        node = LocalNode(path=path, id=id, master=self, settings=settings)
        self.spawn_thread(node.serve, settings['address'])
        self._node_map[id] = node
        self.vassals.append(node)
        return node
    
    def delete_node(self, id):
        node = self.get_node(id)
        if (not node in self.vassals):
            return False
        if (not node):
            return True
        node.terminate()
        self.vassals.remove(node)
        del self._node_map[node.id]
        return True
    
    def get_node(self, id):
        return self._node_map.get(id, None)
    
    def identify_nodes(self, nodes):
        raise NotImplementedError()
    
    def file_operations(self, operations):
        raise NotImplementedError()
    
    def recognize(self, node):
        self.master = node
        logging.info("We recognize: %r" % (node.address,))

    def _terminate(self, recurse):
        logging.info("Sovereign server terminating...")
        eventlet.sleep(.01)
        if recurse:
            for vassal in self.vassals:
                vassal.terminate()
                del self._node_map[vassal.id]
        if (self._socket):
            self.close()
            sys.exit(0)

    def terminate(self, recurse=True):
        self.stop()
        if (self._socket):
            eventlet.spawn_n(self._terminate, recurse)
            return True
        return False