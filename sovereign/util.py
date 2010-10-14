"""
    Utility functions
"""

def eat_path_info(environ, part):
    environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'] + part
    environ['PATH_INFO'] = environ['PATH_INFO'][len(part):]
    return environ

import logging
class FileLikeLogger(object):
    """
        Acts like a file, but just logs to the logger.
    """
    def __init__(self, name=None, level="info"):
        if name:
            self.logger = logging.getLogger(name)
        else:
            self.logger = logging.getLogger()
        self.level = level
    
    def write(self, output):
        getattr(self.logger, self.level)(output.strip())


def path_insert(dct, k, v):
    """ 
        Ensures the key *k* in dct, and then inserts a path like the os PATH
        into that value.
    """
    if k in dct:
        dct[k] = "%s:%s" % (v, dct[k])
    else:
        dct[k] = v


import shlex
from eventlet.green import subprocess
def shell(path, cmd):
    args = shlex.split(str(cmd))
    try:
        popen = subprocess.Popen(list(args), cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = popen.communicate()
    except OSError, e:
        err = str(e)
        out = None
    
    return out, err


class MutableFile(object):
    """
    A MutableFile is like a file, except that it will keep a cache of the
    file's contents until the file is updated.
    """
    def __init__(self, path):
        self.path = path
        self.mtime = -1
        self.read()
    
    def is_stale(self):
        try:
            mtime = os.stat(self.path).st_mtime
        except:
            return True
        if mtime > self.mtime:
            self.mtime = mtime
            return True
        return False
    
    def read(self):
        if self.is_stale():
            file = open(self.path)
            try:
                self.cache = file.read()
            finally:
                file.close()
        return self.cache
    
    def reset(self):
        self.mtime = -1