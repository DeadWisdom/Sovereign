import os
import urlparse, rfc822
from eventlet.green import urllib2
from tempfile import TemporaryFile

from file import DeploymentBase, Deployment as FileDeployment

class Deployment(FileDeployment):
    def acquire(self):
        response = urllib2.urlopen('http:%s' % self.src)
        
        tmpfile = TemporaryFile()
        while True:
            r = response.read(4096)
            if not r: break
            tmpfile.write(r)
        tmpfile.seek(0)
        
        filename = urlparse.urlsplit(response.geturl()).path.rsplit('/', 1)[1]
        self.unpack(tmpfile, filename)
        return True
    
    def is_stale(self, path):
        con, url = self.get_connection('HEAD', self.src)
        con.request('HEAD', url)
        response = con.getresponse()
        return rfc822.parsedate(response.getheader('last-modified'))

Deployment.register('http')