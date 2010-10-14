import os
from sovereign import http, service, template, util, static

MEDIA_PATH = os.path.abspath(
    os.path.join( os.path.dirname(__file__), 'media' )
)

class Service(service.Service):
    def init(self):
        self._index = util.MutableFile( os.path.join(MEDIA_PATH, 'index.html') )
        self._media = static.Static( root = MEDIA_PATH, volatile = True )
    
    def route(self, env):
        if (env['PATH_INFO'] == '/'):
            return self.index(env)
        if (env['PATH_INFO'].startswith('/media')):
            util.eat_path_info(env, '/media')
            return self._media
    
    def index(self, env):
            content = template.simple_template(self._index.read(), {
                'url': env['PATH_INFO'],
                'title': 'Administration',
                'msg': 'We are sovereign',
            })
            return http.Response(content=content)
    
    def services(self, environ, start_response):
        path = environ['PATH_INFO']
        if path == '*.json':
            root = os.path.abspath( self._manager.path )
            services = []
            for token in self._manager.services:
                services.append(token.info())
            services.sort(key=lambda x: x.get('name', '-'))
            content = simplejson.dumps(services)
            return http.Response(content=content, type='text/javascript')(environ, start_response)