from sovereign.deployment import Deployment
import os, shutil, eventlet


class Setting(object):
    def __init__(self, key=None, default=None, type=None, help=None):
        self.key = key
        self.default = default
        self.help = help
        self.type = type


class Service(object):
    settings = [
        Setting('id', None, str),
        Setting('disabled', False, bool),
    ]
    
    def __init__(self, node=None, id=None, settings=None):
        self.id = id
        self.node = node
        self._deployment = None
        
        self.path = os.path.join(node.path, 'services', id)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        
        self.started = False
        self.failed = False
        
        self.settings = dict((s.key, s.default) for s in self.settings)
        if (settings):
            self.settings.update(settings)
        
        self.settings['id'] = self.id
        self.settings['path'] = self.path
        
        self.status = "ready"
        if self.settings['disabled']:
            self.status = "disabled"
        
        self.init()
    
    def delete(self):
        self.stop()
        
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
    
    @property
    def disabled(self):
        return self.settings.get('disabled', False)
    
    def info(self):
        return self.settings
    
    def init(self):
        pass
    
    def info(self):
        info = self.settings.copy()
        info['started'] = self.started
        info['failed'] = self.failed
        info['status'] = self.status
        return info
    
    def start(self):
        self.started = True
        self.settings['disabled'] = False
    
    def stop(self):
        if self._deployment:
            self._deployment.cancel()
        self.started = False
    
    def deploy(self):
        """
        If I have a src, go and get that.
        """
        src = self.settings.get('src', None)
        
        if src is not None:
            typ, _, src = src.partition(":")
            self._deployment = Deployment.get_deployment(typ)(self, src)
            self._thread = self.node.spawn_thread( self._deployment.start )
            eventlet.sleep(0)
        else:
            self._thread = self.node.spawn_thread( self.start )
            eventlet.sleep(0)
    
    def disable(self):
        self.stop()
        self.settings['disabled'] = True
        self.status = "disabled"
    
    def tick(self):
        """
            Should return whether it is working or not.
        """
        return True
    
    def route(self, env):
        """
            Allows the service to bind to the rest interface.  Return None if
            the request is not for this service.
        """
        return None
    
    def msg(self, msg, **kwargs):
        key = '%s_msg' % msg
        func = getattr(self, key, None)
        if (func):
            return func(**kwargs)
        raise NameError("No message named %r." % msg)
    