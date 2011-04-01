import os, shutil, eventlet
import logging
import logging.handlers

from sovereign.deployment import Deployment
from sovereign.util import RingHandler, shell
from settings import IdField, BoolField, NoteField, StringList, Settings, Fieldset


logging.MESSAGE = logging.INFO - 1
logging.addLevelName(logging.MESSAGE, 'MESSAGE')


Service = None

class MetaService(type):
    def __new__(cls, name, bases, attrs):
        if 'name' not in attrs:
            raise ValueError("Service requires a 'name' attribute.")
        
        new = super(MetaService, cls).__new__(cls, name, bases, attrs)
        if Service:
            Service.classes[attrs['name']] = new
        else:
            new.classes[attrs['name']] = new
        
        new.fields = []
        for base in bases:
            if hasattr(base, 'fields'):
                new.fields.extend( base.fields )
        
        if 'settings' in attrs:
            new.fields.append(Fieldset(attrs['name'], attrs['settings']))
        
        return new


class Service(object):
    __metaclass__ = MetaService
    name = "basic"

    classes = {}
    settings = [
        IdField('id', None),
        NoteField('description', ''),
        BoolField('disabled', False),
        StringList('deploy', [], "Commands to execute at the end of deployment."),
    ]
    
    def __init__(self, node=None, id=None, settings=None):
        self.id = id
        self.node = node
        self._deployment = None
        self._last_returncode = None
        
        self.path = os.path.join(node.path, 'services', id)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            
        self._log_path = os.path.join(node.path, 'logs', id)
        if not os.path.exists(self._log_path):
            os.makedirs(self._log_path)
        
        self.create_logger(self.node.log_level)
        
        self.started = False
        self.failed = False
        
        user_settings = settings or {}
        user_settings['path'], user_settings['id'] = self.path, self.id
        
        self.settings = Settings(["default", "config", "user"])
        self.settings.extend(self.__class__.fields)
        self.settings.update(user_settings, "user")
        
        self.status = "ready"
        if self.settings['disabled']:
            self.status = "disabled"
            
        self._thread = None           # Primary thread
        self._ticker = None           # Ticker thread
        
        self.init()
    
    def command(self, *args, **kw):
        self.logger.info("> " + " ".join(args))
        out, err, returncode = shell(self.path, " ".join(args))
        
        if err:
            self.logger.error(err)
            
        if out:
            if not kw.get('suppress_out', False):
                self.logger.info(out)
        
        self._last_returncode = returncode
        
        return out, err
    
    def delete(self):
        self.stop()
        
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        
        self.logger.info("service deleted.")
    
    @property
    def disabled(self):
        return self.settings.get('disabled', False)
    
    def info(self):
        return self.settings
    
    def init(self):
        pass
    
    def info(self):
        info = self.settings.flat()
        info['started'] = self.started
        info['failed'] = self.failed
        info['status'] = self.status
        return info
    
    def start(self):
        if (self.started): return
        self.failed = False
        self.logger.info("starting service...")
        self.started = True
        self.settings['disabled'] = False
        self.msg('start')
        self._ticker = self.node.spawn_thread( self._tick )
    
    def stop(self):
        if self._deployment:
            self._deployment.cancel()
        if (self._ticker):
            self._ticker.kill()
            self._ticker = None
        if (self._thread):
            self._thread.kill()
            self._thread = None
        self.msg('stop')
        self.started = False
        self.logger.info("service stopped.")
    
    def deploy(self):
        """
        If I have a src, go and get that.
        """
        
        src = self.settings.get('src', None)
        
        if src is not None:
            typ, _, src = src.partition(":")
            self._deployment = Deployment.get_deployment(typ)(self, src)
        else:
            self._deployment = Deployment(self, None)
        
        self._thread = self.node.spawn_thread( self._deployment.start )
        eventlet.sleep(0)
    
    def disable(self):
        self.stop()
        self.settings['disabled'] = True
        self.status = "disabled"
        self.logger.info("service disabled.")
    
    def enable(self):
        self.settings['disabled'] = False
        self.status = "enabled"
        self.logger.info("service enabled.")
        self.deploy()
    
    def _tick(self):
        while self.started and not self.failed:
            self.tick()
            eventlet.sleep(.1)
    
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
    
    def redeploy_msg(self):
        self.node.modify_service(self.id, {})
    
    def start_msg(self):
        pass
    
    def stop_msg(self):
        pass
    
    def enable_msg(self):
        self.enable()
    
    def disable_msg(self):
        self.disable()
    
    def deploy_msg(self):
        for cmd in self.settings['deploy']:
            cmd = cmd.strip()
            if not cmd or cmd.startswith('#'): continue
            self.command(cmd)
            if self._last_returncode != 0:
                raise RuntimeError("Error in deployment script.")
    
    def deploy_failed_msg(self):
        pass
    
    def msg(self, msg, **kwargs):
        key = '%s_msg' % msg
        func = getattr(self, key, None)
        if (func):
            self.logger.log(logging.MESSAGE, msg)
            return func(**kwargs)
        raise NameError("No message named %r." % msg)
    
    def create_logger(self, verbosity=logging.DEBUG ):
        if self.id in logging.Logger.manager.loggerDict:
            self.logger = logging.getLogger(self.id)
            self._log = self.logger.ring
            return self.logger
        
        path = os.path.join(self._log_path, 'log.txt')
        
        file_handler = logging.handlers.RotatingFileHandler(path, maxBytes=2**24, backupCount=5)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(verbosity)
        stream_handler.setFormatter(
            logging.Formatter("%(levelname)s - %(name)s - %(message)s")
        )
        
        ring_handler = self._log = RingHandler()
        ring_handler.setLevel(logging.MESSAGE)
        ring_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        
        self.logger = logging.getLogger(self.id)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(ring_handler)
        self.logger.ring = ring_handler
        
        return self.logger