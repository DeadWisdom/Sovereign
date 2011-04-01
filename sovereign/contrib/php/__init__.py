"""
PHP Service.
"""
import os, shutil, sys

from eventlet.green import socket
from sovereign import service
from sovereign.contrib.web.fastcgi import FastCGI
from sovereign.contrib.web.static import Static
from sovereign.util import find_empty_port


class PhpService(service.ProcessService):
    name = "php"
    
    settings = [
        service.AddressField('address', ('localhost', 0)),
        service.StringField('ini', None),
        service.StringDict('options', {}),
        service.StringList('indexes', ['index.php', 'index.html']),
        
        service.StringField('web.host', '*')
    ]
    
    def start(self):
        address = self.settings['address']
        args = self.settings['args']
        options = self.settings['options']
        ini = self.settings['ini']
        
        if (address[1] == 0):
            self.address = find_empty_port()
        else:
            self.address = address
        
        if not args:
            args = ['-b', '%s:%s' % self.address]
            if ini:
                args.extend(['-c', ini])
            for pair in options.items():
                args.extend(['-d', '%s=%s' % pair])
            if not 'doc_root' in options.keys():
                args.extend(['-d', 'doc_root=%s' % self.path])
        
        self.settings['args'] = args
        self.settings['executable'] = 'php-cgi'
        
        super(PhpService, self).start()
        
        self._static = Static(indexes=self.settings['indexes'], root=self.path, allow=None)
        self._static.set_handler('php', self._handle)
        
        self._fastcgi = FastCGI(self.address)
    
    def route_msg(self, environ=None, start_response=None):
        if 'REQUEST_URI' not in environ:
            # PHP likes to have this variable
            request_uri = [
                environ.get('SCRIPT_NAME', ''),
                environ.get('PATH_INFO', ''),
            ]
            if environ.get('QUERY_STRING'):
                request_uri.extend(['?', environ['QUERY_STRING']])
            environ['REQUEST_URI'] = "".join(request_uri)
            
        path = environ['PATH_INFO']
        if '.php/' in path:
            path, info = path.split('.php/', 1)
            environ['PATH_INFO'] = path + '.php'
            environ['minister.php_info'] = '/' + info
        
        return self._static(environ, start_response)
        
    def _handle(self, environ, start_response, path):
        _SERVER = environ
        
        _SERVER['SCRIPT_NAME'] = environ['SCRIPT_NAME'] + environ['PATH_INFO'] 
        _SERVER['SCRIPT_FILENAME'] = path    
        _SERVER["DOCUMENT_ROOT"] = self.path
        _SERVER["SERVER_NAME"] = environ["HTTP_HOST"]
        
        if 'minister.php_info' in environ:
            _SERVER['PATH_INFO'] = environ['minister.php_info']
            del _SERVER['minister.php_info']
        else:
            _SERVER['PATH_INFO'] = ''
        
        if (environ['REQUEST_METHOD'] == 'POST' and not environ.get('CONTENT_TYPE')):
            _SERVER['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        
        response = self._fastcgi(_SERVER, start_response)
        return response