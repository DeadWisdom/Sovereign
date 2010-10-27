import os, sys

try:
    import json
except ImportError:
    import simplejson as json

from sovereign.process import Process
from sovereign.util import path_insert
from base import Service
from settings import StringField, StringList, IntegerField, StringDict, BoolField


class ProcessService(Service):
    """
    A process service will run a process when it is started.
    """
    name = "process"
    
    settings = [
        StringField('executable', None, "The executable to run.  If not given, it will default to 'sys.executable' / the python bin used to run sovereign."),
        StringList('args', []),
        IntegerField('count', 1),
        StringDict('environ', {}),
        BoolField('restart', True),
    ]
    
    ### Methods ##########################
    def init(self):
        self._processes = []
    
    def start(self):
        executable = self.settings['executable'] or sys.executable
        args = self.settings['args']
        count = self.settings['count']
        
        environ = self.get_environ()
        self.logger.info("running - %s %s", executable, " ".join(args))
        for i in xrange(count):
            process = Process(self.path, executable, args, environ, self.logger)
            self._processes.append( process )
            process.run()
        
        return super(ProcessService, self).start()
        
    def stop(self):
        for process in self._processes:
            try:
                process.kill()
            except:
                pass
        self._processes = []
        
        super(ProcessService, self).stop()
    
    def get_environ(self):
        """
        This dictionary is added to our environment for a child process.
        """
        environ = os.environ.copy()
        environ.update(self.settings['environ'])
        environ.update({
            'SOVEREIGN_NODE_ID': self.node.id,
            'SOVEREIGN_NODE_ADDRESS': "%s:%s" % self.node.address,
            'SOVEREIGN_NODE_PATH': str(self.node.path),
            'SOVEREIGN_SERVICE_PATH': str(self.path),
            'SOVEREIGN_SERVICE_SETTINGS': json.dumps(self.settings),
        })
        
        # Place our path in the Path:
        path_insert(environ, 'PATH', os.path.abspath(os.curdir))
        path_insert(environ, 'PATH', os.path.abspath(self.path))
        
        environ['OLDPWD'] = environ.get('PWD', '')
        environ['PWD'] = os.path.abspath(self.path) 
        
        return environ
    
    def tick(self):
        """
        This will get the health of the processes, any dead processes will be 
        restarted until they are marked failed.  If strict is true,
        no processes will be restarted; they have to be running or they fail.
        """
        strict = (not self.settings['restart'])
        active = 0
        failed = True
        for process in self._processes:
            if process.check():
                failed = False
                active += 1
            elif process.is_failure() or strict:
                process.kill()
                self._processes.remove(process)
            else:
                failed = False
                process.kill()
                process.run()
        
        self.failed = failed
        
        total = self.settings['count']
        plural = 'es'
        if total == 1:
            plural = ''
        
        if failed:
            self.logger.error("service failed: %s", self.path)
            self.status = "processes failed"
            self.settings['processes'] = '0 of %d process%s' % (total, plural)
            return False, 
        elif active == total:
            self.settings['processes'] = '%d of %d process%s' % (active, total, plural)
        elif active < total:
            self.settings['processes'] = '%d of %d process%s' % (active, total, plural)
