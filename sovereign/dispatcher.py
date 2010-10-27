try:
    import json
except ImportError:
    import simplejson as json

from sovereign import http, util
import logging

### Json Helpers ###
def JsonResponse(data=None, headers=None, type='application/json', status="200 OK"):
    headers = headers or [('Content-Type', type)]
    def app(environ, start_response):
        start_response(status, headers)
        yield json.dumps(data)
    return app


### Dispatcher ###
class Dispatcher(object):
    def __init__(self, node):
        self.node = node;
    
    @property
    def master(self):
        return self.node.master
    
    def route(self, env):
        path = env['PATH_INFO']
        
        if (path == '/info'):
            return self.handle_get('info', env)
            
        if (path == '/sys'):
            return self.handle_post('sys', env)
        
        if (path == '/pip-install'):
            return self.handle_post('pip_install', env)
        
        if (path == '/pip-uninstall'):
            return self.handle_post('pip_uninstall', env)
    
        if (path == '/terminate'):
            return self.handle_post('terminate', env)
        
        if (path == '/recognize'):
            host, port = tuple(json.loads( env['wsgi.input'].read() ))
            host = host or env['REMOTE_ADDR']
            
            from sovereign.node import RemoteNode
            self.node.recognize(RemoteNode(address=(host, port)))
            return JsonResponse(data=True)
        
        if (path.startswith('/services/')):
            return self.handleService(self.node, util.eat_path_info(env, '/services/'))
        
        if (path.startswith('/nodes/')):
            return self.handleNodes(util.eat_path_info(env, '/nodes/'))
    
    def handleService(self, node, env):
        method = env['REQUEST_METHOD'].lower()
        rest = env['PATH_INFO'].rstrip('/').split('/')
        args = util.query_args(env)
        
        if len(rest) == 1:
            id = rest[0]
            # continued below
        elif len(rest) == 2:
            id = rest[0]
            if (method == 'get' and rest[1] == 'log'):
                try:
                    since = int(args.get('since', [0])[0])
                    log = node.get_service_log(id, since=since)
                except:
                    logging.exception("Error")
                    return None
                return JsonResponse(data=log)
            elif (method == 'post' and rest[1] == 'delete'):
                 return JsonResponse(data=node.delete_service(id))
            elif (method == 'post' and rest[1].startswith('~')):
                kwargs = json.loads( env['wsgi.input'].read() )
                response = node.msg_service(id, rest[1][1:], **kwargs)
                return JsonResponse(data=response)
            else:
                return http.NotFound()
        else:
            return http.NotFound()
        
        if (method == 'put'):
            if (node.get_service(id)):
                return http.MethodNotAllowed(['GET', 'POST', 'DELETE'])
            
            settings, = json.loads( env['wsgi.input'].read() )
            service = node.create_service(id, settings)
            return JsonResponse(data=service)
        
        if (method == 'post'):
            settings = json.loads( env['wsgi.input'].read() )
            service = node.modify_service(id, settings)
            return JsonResponse(data=service)
        
        if (method == 'get'):
            service = node.get_service(id)
            if service:
                return JsonResponse(data=service)
            else:
                return None
        
        if (method == 'delete'):
            return JsonResponse(data=node.delete_service(id))
    
    def handleNodes(self, env):
        method = env['REQUEST_METHOD'].lower()
        rest = env['PATH_INFO'].rstrip('/').split('/')
        id = rest[0]
        
        if len(rest) > 1:
            node = self.node.get_node(id)
            if not node:
                return http.NotFound("Unknown node: %r" % id)
            return self.handleService(node, util.eat_path_info(env, '%s/' % id))
        
        if (method == 'put'):
            existing = self.node.get_node(id)
            if (existing):
                if (existing in self.node.vassals):
                    return http.MethodNotAllowed(['GET', 'DELETE'])
                else:
                    return http.MethodNotAllowed(['GET'])
            
            path, settings = json.loads( env['wsgi.input'].read() )
            node = self.node.create_local_node(id, path, settings)
            return JsonResponse(data=node.info())
            
        if (method == 'get'):
            node = self.node.get_node(id)
            if node:
                return JsonResponse(data=node.info())
            else:
                return None
        
        if (method == 'delete'):
            return JsonResponse(data=self.node.delete_node(id))
    
    def handle_post(self, cmd, env):
        args = json.loads( env['wsgi.input'].read() )
        return JsonResponse(data=getattr(self.node, cmd)(*args))
    
    def handle_get(self, cmd, env):
        return JsonResponse(data=getattr(self.node, cmd)())
        
        