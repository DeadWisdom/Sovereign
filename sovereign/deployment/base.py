import os, shutil
from sovereign.util import shell, json

class DeploymentBase(object):
    _classes = {}
    
    @classmethod
    def register(cls, name):
        DeploymentBase._classes[name] = cls
    
    @classmethod
    def get_deployment(cls, name):
        cls = DeploymentBase._classes.get(name, None)
        if cls is None:
            raise DeploymentNotFound("Cannot find deployment method: %r" % name)
        return cls
    
    def __init__(self, service, src):
        self.service = service
        self.src = src
        self.logger = service.logger
    
    def command(self, *args, **kw):
        return self.service.command(*args, **kw)
    
    def prepare(self):
        try:
            os.makedirs(self.service.path)
        except OSError, e:
            if (e.errno != 17):
                raise
        
        path = os.path.join(self.service.path, 'service.json')
        if os.path.exists(path):
            o = open(path, 'r')
            try:
                self.service.update_settings(repo=json.load(o))
            except:
                self.service.logger.exception("Unable to load service.json")
                pass
            finally:
                o.close()
        
    
    def remove(self):
        shutil.rmtree(self.service.path)
    
    def acquire(self):
        """
        Acquire the src, bring it to the path 
        """
        pass
    
    def unpack(self, package, filename):
        pass
    
    def start(self):
        try:
            self.logger.info("deploying service...")
            self.service.status = "deploying"
            self.prepare()
            self.acquire()
            self.service.msg('deploy')
            self.service.status = "ready"
            self.service.start()
        except Exception, e:
            self.logger.exception('deployment failed.')
            self.cancel()
            self.service.msg('deploy_failed')
            self.service.failed = True
            self.service.status = "deployment failed"

    def cancel(self):
        pass

Deployment = DeploymentBase

class DeploymentNotFound(Exception):
    pass
    
class DeploymentFailed(Exception):
    pass
