import os
from base import DeploymentBase, DeploymentFailed

class Deployment(DeploymentBase):
    def has_hg(self, path):
        return os.path.exists(os.path.join(path, '.hg'))
    
    def acquire(self):
        path = self.service.path
        if self.has_hg(path):
            out, err, _ = self.command("hg", "pull", "-u", timeout=5)
            if out.find('no changes found') >= 0:
                return False
            return True
        else:
            out, err, _ = self.command("hg", "clone", self.src, path)
            if out.startswith('abort'):
                raise DeploymentFailed(out)
            return True

Deployment.register('hg')
