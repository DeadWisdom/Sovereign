"""
    The Node package describes nodes, the main interface of sovereign.
    
    See base.py for the interface Node().
"""

from local import LocalNode
from remote import RemoteNode


import eventlet

def create_node(settings):
    typ = settings['type']
    if (typ == 'local'):
        node = LocalNode(path=settings['path'], id=settings['id'])
        eventlet.spawn(node.serve, tuple(settings['address']))
        eventlet.sleep(0)
    return node