import os
from base import DeploymentBase, DeploymentFailed

class Deployment(DeploymentBase):
    def acquire(self):
        src = os.path.abspath( self.src )
        dest = os.path.abspath( self.service.path )
        if os.path.isdir(src):
            src = src + '/'
        if os.path.isdir(dest):
            dest = dest + '/'
        out, err = self.command("rsync", '-azri', src, dest, suppress_out=True)
        if err:
            raise DeploymentFailed(err)
        if out:
            return True
        return False


Deployment.register('rsync')