import os, shutil

from eventlet.green import socket
from sovereign import service


class WsgiService(service.PythonService):
    name = "wsgi"
    server_file = '_wsgi.py'
    
    settings = [
        service.AddressField('address', ('localhost', 0)),
        service.IntegerField('threads', 0),
        service.StringField('app', ''),
        service.StringField('web.host', '*'),
        service.StringDict('web.static', {}),
    ]
    
    def init(self):
        self._socket = None
        self.address = None
        super(WsgiService, self).init()
        self._requires = ('eventlet',)
    
    def deploy_msg(self):
        server_py = os.path.join(os.path.dirname(__file__), self.server_file)
        destination = os.path.join(self.path, '__server__.py')
        #if not os.path.exists(destination):
        shutil.copyfile(server_py, destination)
        return super(WsgiService, self).deploy_msg()
    
    def start(self):
        if not self.settings['args']:
            self.settings['args'] = ['__server__.py']
        
        self._socket = socket.socket()
        self._socket.bind( tuple(self.settings['address']) )
        self._socket.listen(500)
        self.address = self._socket.getsockname()
        
        return super(WsgiService, self).start()
    
    def stop(self):
        super(WsgiService, self).stop()
        if (self._socket):
            self._socket.close()
            self._socket = None
    
    def get_environ(self):
        host, port = self.address
        
        environ = super(WsgiService, self).get_environ()
        environ['SOVEREIGN_SOCKET'] = str(self._socket.fileno())
        environ['SOVEREIGN_HOST'], environ['SOVEREIGN_PORT'] = host, str(port)
        environ['SOVEREIGN_THREADS'] = str(self.settings['threads'])
        environ['SOVEREIGN_APP'] = self.settings['app']
        environ['SOVEREIGN_VIRTUAL_ENV'] = self.settings['virtualenv']
        return environ


class DjangoService(WsgiService):
    name = "django"
    server_file = "_django.py"
    
    settings = [
        service.StringField('settings', 'settings', "Django settings module.")
    ]
    
    def init(self):
        super(DjangoService, self).init()
        self._requires = self._requires + ('django',)
        
    def get_environ(self):
        environ = super(DjangoService, self).get_environ()
        environ['DJANGO_SETTINGS_MODULE'] = self.settings['settings']
        return environ
