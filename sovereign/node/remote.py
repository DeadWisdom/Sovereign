import logging

try:
    import json
except ImportError:
    import simplejson as json

from eventlet.green import httplib
from base import Node

class RemoteError(Exception):
    def __init__(self, response):
        self.status = response.status
        self.response = response
        super(RemoteError, self).__init__(self, "Bad status from the server: %r" % self.status)

class RemoteNode(Node):
    def __init__(self, address=('127.0.0.1', 1648), settings=None):
        self.address = address
        self.settings = settings or {}
    
    def get_connection(self):
        return httplib.HTTPConnection(self.address[0], self.address[1], timeout=10)
        
    def post(self, url, *args):
        conn = self.get_connection()
        conn.request("POST", url, json.dumps(args))
        response = conn.getresponse()
        if (response.status != 200):
            raise RemoteError(response)
        return json.loads( response.read() )
    
    def put(self, url, *args):
        conn = self.get_connection()
        conn.request("PUT", url, json.dumps(args))
        response = conn.getresponse()
        if (response.status != 200):
            raise RemoteError(response)
        return json.loads( response.read() )
    
    def get(self, url):
        conn = self.get_connection()
        conn.request("GET", url)
        response = conn.getresponse()
        if (response.status != 200):
            raise RemoteError(response)
        return json.loads( response.read() )
        
    def delete(self, url):
        conn = self.get_connection()
        conn.request("DELETE", url)
        response = conn.getresponse()
        if (response.status != 200):
            raise RemoteError(response)
        return json.loads( response.read() )
    
    ### Implementations ###
    def sys_install(self, packages):
        raise NotImplementedError()
    
    def sys_uninsall(self, packages):
        raise NotImplementedError()
    
    def pip_install(self, packages, env=None):
        return tuple( self.post('/pip-install', packages, env) )
    
    def pip_uninstall(self, packages, env=None):
        return tuple( self.post('/pip-uninstall', packages, env) )
    
    def sys(self, cmds):
        return tuple( self.post('/sys', cmds) )
    
    def info(self):
        return self.get('/info')
    
    def create_service(self, id, settings):
        return self.put('/services/%s' % id, settings)
        
    def modify_service(self, id, settings):
        return self.post('/services/%s' % id, settings)
    
    def get_service(self, id):
        try:
            return self.get('/services/%s' % id)
        except RemoteError, e:
            if e.status == 404:
                return None
        
    def delete_service(self, id):
        return self.delete('/services/%s' % id)
    
    def create_local_node(self, id=None, path=None, settings=None):
        settings = self.put('/nodes/%s' % id, path, settings)
        return RemoteNode(address=settings['address'], settings=settings)
    
    def delete_node(self, id):
        return self.delete('/nodes/%s' % id)
    
    def get_node(self, id):
        try:
            return self.get('/nodes/%s' % id)
        except RemoteError, e:
            if e.status == 404:
                return None
    
    def identify_nodes(self, nodes):
        raise NotImplementedError()
    
    def file_operations(self, operations):
        raise NotImplementedError()
    
    def recognize(self, node):
        return self.post('/recognize', node.address[0], node.address[1])
    
    def terminate(self, recurse=True):
        return self.post('/terminate', recurse)
