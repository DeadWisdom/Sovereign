import os
from base import DeploymentBase, DeploymentFailed

class Deployment(DeploymentBase):
    def has_git(self, path):
        return os.path.exists(os.path.join(path, '.git'))
    
    def acquire(self):
        src = self.src
        if src.startswith('//'):
            src = 'git:' + src
        if src.startswith('@'):
            src = 'git' + src
        
        path = self.service.path
        if self.has_git(path):
            cwd = os.path.abspath('.')
            os.chdir(path)
            out, err = self.command("git", "pull")
            os.chdir(cwd)
            if err:
                raise DeploymentFailed(err)
            return out.find("Already up-to-date") == -1
        else:
            out, err = self.command("git", "clone", src, path)
            if err:
                raise DeploymentFailed(err)                
            return True

Deployment.register('git')
