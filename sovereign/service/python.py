import os

from sovereign.util import shell, path_insert
from process import ProcessService, Setting

class PythonService(ProcessService):
    settings = ProcessService.settings + [
        Setting('virtualenv', 'env', str),
        Setting('requires', (), tuple),
    ]
    
    def start(self):
        virtualenv = self.settings['virtualenv']
        requires = self.settings['requires']
        
        if virtualenv and requires:
            cmd = 'pip install -E %s %s' % (virtualenv, " ".join(requires))
            out, err = shell(self.path, cmd)
        
            if err:
                if "mysql-python" in self.requires:
                    logging.warning("mysql-python might require 'mysql_config'; 'apt-get install libmysqlclient-dev' or your package management equivalent might fix this problem.")
                logging.error('> %s\n%s', cmd, err)
                self.stop()
                return False
            elif out:
                logging.info('> %s\n%s', cmd, out)
        
        return super(PythonService, self).start()
    
    def get_environ(self):
        environ = super(PythonService, self).get_environ()
        
        ### Put our virtual env in the environ
        virtualenv = self.settings['virtualenv']
        if virtualenv:
            path = os.path.abspath(os.path.join(self.path, virtualenv))
            environ['VIRTUAL_ENV'] = path
            logging.info("Using virtualenv: %s", path)
            path_insert(environ, 'PATH', os.path.join(path, 'bin'))
        
        path_insert(environ, 'PYTHONPATH', os.path.abspath(os.curdir))
        path_insert(environ, 'PYTHONPATH', os.path.abspath(self.path))
        
        return environ
