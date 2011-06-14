#!/usr/bin/python
import os, sys, logging, shutil
from unittest import TestCase

import eventlet
from sovereign.node import LocalNode


class TestRedis(TestCase):
    address = ('', 1648)
    
    def setUp(self):
        path = os.path.join(os.path.dirname(__file__), 'test_redis')
        if (os.path.exists(path)):
            shutil.rmtree(path)
        
        self.node = LocalNode(path=path, id='test_redis')
        self._server = eventlet.spawn(self.node.serve, self.address)
        self.node.nanny()
    
    def tearDown(self):
        self.node.terminate()
        self._server.kill()
        eventlet.sleep(0)
        try:
            shutil.rmtree(os.path.join(os.path.dirname(__file__), 'test_redis'))
        except:
            pass
    
    def test_redis(self):
        redis = {
            'type': 'sovereign.contrib.redis.Service',
        }
        self.node.create_service('redis', redis)
        self.assertFalse(self.node._get_service('redis').failed)