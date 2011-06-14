import os

from sovereign.util import shell, path_insert
from process import ProcessService
from settings import StringField, StringList

class PythonService(ProcessService):
    settings = [
        StringField('virtualenv', 'env'),
        StringList('requires', ()),
    ]
    
    name = "python"
    
    def init(self):
        self._requires = ()
        super(PythonService, self).init()
    
    def start(self):
        if self.settings['virtualenv'] and not self.settings['executable']:
            self.settings['executable'] = os.path.join(self.settings['virtualenv'], 'bin', 'python')
        return super(PythonService, self).start()
    
    def deploy_msg(self):
        virtualenv = self.settings['virtualenv']
        requires = set(self.settings['requires'] + self._requires)
        
        if virtualenv:
            for req in requires:
                cmd = 'pip -E %s install %s' % (virtualenv, req)
                out, err, _ = self.command(cmd)
        
                if err:
                    if "mysql-python" in self.requires:
                        self.logger.warning("mysql-python might require 'mysql_config'; 'apt-get install libmysqlclient-dev' or your package management equivalent might fix this problem.")
                    if (self._last_returncode != 0):
                        raise RuntimeError("Error installing python packages.")
        
        return super(PythonService, self).deploy_msg()
    
    def get_environ(self):
        environ = super(PythonService, self).get_environ()
        
        ### Put our virtual env in the environ
        virtualenv = self.settings['virtualenv']
        if virtualenv:
            path = os.path.abspath(os.path.join(self.path, virtualenv))
            environ['VIRTUAL_ENV'] = path
            self.logger.info("Using virtualenv: %s", path)
            path_insert(environ, 'PATH', os.path.join(path, 'bin'))
        
        path_insert(environ, 'PYTHONPATH', os.path.abspath(os.curdir))
        path_insert(environ, 'PYTHONPATH', os.path.abspath(self.path))
        
        return environ
