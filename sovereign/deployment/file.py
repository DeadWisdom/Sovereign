import os, shutil
import tarfile, zipfile

from base import DeploymentBase, DeploymentFailed


class Deployment(DeploymentBase):
    def acquire(self):
        self.remove()
        if os.path.isdir(self.src):
            shutil.copytree(self.src, self.service.path)
        else:
            self.unpack(open(self.src, 'rb'), os.path.basename(self.src))
        return True

    def unpack(self, package, filename):
        path = self.service.path
        
        self.prepare()
            
        if filename.endswith('.zip'):
            archive = zipfile.ZipFile(file=package)
            archive.extractall(path=path, members=self.zip_members(archive))
            archive.close()
        else:
            if filename.endswith('.tar.gz') or filename.endswith('.tgz'):
                mode = 'r:gz'
            elif filename.endswith('.tar.bz2') or filename.endswith('.tbz2'):
                mode = 'r:bz2'
            elif filename.endswith('.tar'):
                mode = 'r'
            else:
                return
            
            archive = tarfile.open(fileobj=package, mode=mode)
            try:
                archive.extractall(path=path, members=self.tar_members(archive))
            finally:
                archive.close()
    
    def tar_members(self, archive):
        """If the tar only has one directory, here we make it instead be that directorie's contents."""
        roots = set(name.partition('/')[0] for name in archive.getnames())
        if len(roots) > 1:
            return
        for member in archive.getmembers():
            member.name = member.name.partition('/')[2]
            if member.name and '..' not in member.name:
                yield member
    
    def zip_members(self, archive):
        roots = set(name.partition('/')[0] for name in archive.namelist() if not name.startswith('__'))
        if len(roots) > 1:
            return
        for name in archive.namelist():
            n = name.partition('/')[2]
            if n and '..' not in n and not name.startswith('__'):
                yield name


Deployment.register('file')