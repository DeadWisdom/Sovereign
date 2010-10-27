import logging

from base import Service
from process import ProcessService
from python import PythonService

from settings import *

def get_service_class(sig):
    from sovereign import contrib
    
    try:
        return Service.classes[sig]
    except:
        pass
    
    try:
        module, cls = sig.rsplit('.', 1)
        cls = cls.encode()
    except:
        logging.error("Service class name is not formatted correctly: %r" % sig)
        return None
        
    try:
        mod = __import__(module, {}, {}, [cls])
    except:
        logging.exception("Unable to import the service class: %r" % sig)
        raise
    
    return getattr(mod, cls)

class ServiceIdCollision(Exception):
    """
    Exception raised when trying to create a new service with an id of an
    already existing service.
    """
    pass