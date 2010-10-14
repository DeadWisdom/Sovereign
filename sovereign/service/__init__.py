import logging

from base import Service, Setting
from process import ProcessService
from python import PythonService

def get_service_class(import_path):
    try:
        module, cls = import_path.rsplit('.', 1)
        cls = cls.encode()
    except:
        logging.error("Service class name is not formatted correctly: %r" % import_path)
        return None
        
    try:
        mod = __import__(module, {}, {}, [cls])
    except:
        logging.exception("Unable to import the service class: %r" % import_path)
        raise
    
    return getattr(mod, cls)

class ServiceIdCollision(Exception):
    """
    Exception raised when trying to create a new service with an id of an
    already existing service.
    """
    pass