import os, shutil, logging
from sovereign.util import shell

CMD = logging.INFO-1
logging.addLevelName(CMD, "CMD")

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
    
    def command(self, *args, **kw):
        logging.log(CMD, " ".join(args))
        out, err = shell(self.service.path, " ".join(args))
        
        if err:
            for line in err.split('\n'):
                logging.info('    ' + line)
            
        if out:
            if not kw.get('suppress_out', False):
                for line in out.split('\n'):
                    logging.info('    ' + line)
        
        return out, err
    
    def prepare(self):
        try:
            os.makedirs(self.service.path)
        except OSError, e:
            if (e.errno != 17):
                raise
    
    def remove(self):
        shutil.rmtree(self.service.path)
    
    def acquire(self):
        """
        Acquire the src, bring it to the path 
        """
        raise NotImplementedError()
    
    def unpack(self, package, filename):
        pass
    
    def start(self):
        try:
            self.service.status = "deploying"
            self.prepare()
            self.acquire()
            self.service.status = "ready"
            self.service.start()
        except Exception, e:
            logging.exception('Deployment failed.')
            self.cancel()
            self.service.failed = True
            self.service.status = "deployment failed"

    def cancel(self):
        pass

Deployment = DeploymentBase


class DeploymentNotFound(Exception):
    pass
    
class DeploymentFailed(Exception):
    pass
