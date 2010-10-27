"""
    Utility functions
"""
import os

try:
    import json
except ImportError:
    import simplejson as json


def eat_path_info(environ, part):
    environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'] + part
    environ['PATH_INFO'] = environ['PATH_INFO'][len(part):]
    return environ


import cgi
def query_args(environ):
    query = environ.get("QUERY_STRING", "")
    if query:
        return cgi.parse_qs(query)
    return {}


def path_insert(dct, k, v):
    """ 
        Ensures the key *k* in dct, and then inserts a path like the os PATH
        into that value.
    """
    if k in dct:
        dct[k] = "%s:%s" % (v, dct[k])
    else:
        dct[k] = v


def fix_unicode_keys(o):
    """
    Fixes all key, value pairs to be str(key), value pairs.
    """
    if isinstance(o, dict):
        return dict( (str(k), fix_unicode_keys(v)) for k, v in o.items() )
    elif hasattr(o, '__iter__') and not isinstance(o, basestring):
        return [ fix_unicode_keys(v) for v in o ]
    return o


def random_str():
    import hashlib
    h = hashlib.new('md5')
    h.update(os.urandom(128))
    return h.hexdigest()
    

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
    
    return out, err, popen.returncode


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


__used_addresses = set()
def find_empty_port(host='localhost', ports=(10000, 20000)):

    for port in range(*ports):
        if (host, port) in __used_addresses:
            continue
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except socket.error, e:
            continue
        else:
            __used_addresses.add((host, port))
            s.close()
            return host, port


import logging
class FileLikeLogger(object):
    """
        Acts like a file, but just logs to the logger.
    """
    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level
    
    def write(self, output):
        self.logger.log(logging.INFO, output.strip())


class RingHandler(logging.Handler):
    def __init__(self, max_entries=500):
        self.max_entries = max_entries
        self.position = 0
        self.data = [None] * self.max_entries
        logging.Handler.__init__(self)
    
    def iter_tail(self, len=None):
        if len is None or len > self.max_entries:
            len = self.max_entries
        
        pos = self.position - 1
        total = 0
        while pos >= 0 and total < len:
            item = self.data[pos]
            if item is None:
                return 
            yield item
            total += 1
            pos -= 1
        
        pos = self.max_entries - 1
        while pos >= self.position and total < len:
            item = self.data[pos]
            if item is None:
                return 
            yield item
            total += 1
            pos -= 1

    def get_lines(self):
        if self.data[-1] is None:
            return self.data[:self.position]
        return self.data[self.position:] + self.data[:self.position]
    
    def get_lines_since(self, since):
        for item in self.iter_tail():
            if int(item['created']) <= since:
                return
            yield item
    
    def read(self):
        return "\n".join(self.get_lines())
    
    def emit(self, record):
        message = getattr(record, 'message', str(record))
        self.data[self.position] = {
            'levelname': record.levelname,
            'levelno': 20,
            'created': record.created,
            'filename': record.filename,
            'funcName': record.funcName,
            'message': message,
        }
        self.position = (self.position + 1) % self.max_entries
