import os

from test_node import TestNode
from sovereign.node import RemoteNode

class TestRemote(TestNode):
    ports = [1648, 1650]
    
    def setUp(self):
        super(TestRemote, self).setUp()
        self.node = RemoteNode(address=self._local.address, key=self._local.key)

del TestNode

"""
addresses = node.create_nodes([{
'type': 'local',
'path': '/projects/sovereign/sandbox',
'serve': ('127.0.0.1', 1650),
}])
"""