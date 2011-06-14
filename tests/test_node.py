#!/usr/bin/python
import os, sys, logging, shutil, random
from unittest import TestCase

import eventlet
from eventlet.timeout import Timeout
from sovereign.node import LocalNode


class TestNode(TestCase):
    ports = [random.randint(1640, 5640), random.randint(1640, 5640)]
    paths = ['nodeA', 'nodeB']
    
    def setUp(self):
        path = os.path.join(os.path.dirname(__file__), self.paths[0])
        if (os.path.exists(path)):
            shutil.rmtree(path)
        
        self._local = LocalNode(path=path, id='nodeA')
        self.node = self._local
        
        self._server = eventlet.spawn(self._local.serve, ('127.0.0.1', self.ports[0]))
        self.node.nanny()
    
    def tearDown(self):
        self._server.kill()
        eventlet.sleep(0)
        for p in self.paths:
            try:
                shutil.rmtree(os.path.join(os.path.dirname(__file__), p))
            except:
                pass
    
    def test_local(self):
        self.assertEqual(self._local.master, self._local)
        self.assertEqual(self._local.address, ('127.0.0.1', self.ports[0]))
        self.assertTrue( os.path.exists( os.path.join(self._local.path, 'settings.json') ) )

    def test_sys(self):
        stdout, stdin = self.node.sys(['echo true'])
        eventlet.sleep(0)
        self.assertEqual( stdout[0].strip(), "true" )
    
    def test_create_node(self):
        path = os.path.join(os.path.dirname(__file__), self.paths[1])
        node = self.node.create_local_node('nodeB', path, {
            'address': ('127.0.0.1', self.ports[1]),
        })
        self.assertTrue(os.path.exists(path))
        
    def test_info(self):
        info = self.node.info()
        self.assertEqual(tuple(info['address']), ('127.0.0.1', self.ports[0]))
    
    def test_basic_service(self):
        basic = {
            'type': 'sovereign.service.base.Service'
        }
        service = self.node.create_service('basic', basic)
        self.assertEqual(service['id'], 'basic')
        
        path = os.path.join(self._local.path, 'basic')
        self.assertTrue( os.path.exists(path) )
        
        self.assertEqual( service, self.node.get_service('basic') )
        
        self.node.modify_service('basic', basic)
        
        self.node.delete_service('basic')
        self.assertFalse( os.path.exists(path) )
        self.node.delete_service('basic')
    
    def test_zzz_terminate(self):
        success = self.node.terminate()
        self.assertTrue(success)
        #self.assertEqual(self._local.address, None)
    