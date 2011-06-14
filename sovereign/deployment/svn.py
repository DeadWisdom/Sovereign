import os
from base import DeploymentBase, DeploymentFailed

class Deployment(DeploymentBase):
    def acquire(self):
        path = self.service.path        
        out, err, _ = self.command("svn", "checkout", self.src, self.service.path)
        if err:
            raise DeploymentFailed(err)
        return not out.startswith('Checked out revision')

Deployment.register('svn')
