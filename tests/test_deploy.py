#!/usr/bin/python
import os, sys, logging, shutil
from unittest import TestCase

import eventlet
from sovereign.node import LocalNode


class TestNode(TestCase):
    ports = [1648, 1649]
    paths = ['nodeA', 'nodeB']
    
    def setUp(self):
        path = os.path.join(os.path.dirname(__file__), self.paths[0])
        if (os.path.exists(path)):
            shutil.rmtree(path)
        
        self.node = LocalNode(path=path, id='nodeA')
        self._server = eventlet.spawn(self.node.serve, ('127.0.0.1', self.ports[0]))
        eventlet.sleep(0)
    
    def tearDown(self):
        self.node.terminate()
        self._server.kill()
        eventlet.sleep(0)
        for p in self.paths:
            try:
                shutil.rmtree(os.path.join(os.path.dirname(__file__), p))
            except:
                pass
    
    def test_file_dir(self):
        basic = {
            'type': 'sovereign.service.base.Service',
            'src': 'file:tests/src'
        }
        self.node.create_service('basic', basic)
        self.assertFalse(self.node._get_service('basic').failed)
        self.node.delete_service('basic')
        
    def test_file_tar_gz(self):
        basic = {
            'type': 'sovereign.service.base.Service',
            'src': 'file:tests/src.tar.gz'
        }
        self.node.create_service('basic', basic)
        self.assertFalse(self.node._get_service('basic').failed)
        self.node.delete_service('basic')
    
    def test_rsync(self):
        basic = {
            'type': 'sovereign.service.base.Service',
            'src': 'rsync:tests/src'
        }
        self.node.create_service('basic', basic)
        self.assertFalse(self.node._get_service('basic').failed)
        self.node.delete_service('basic')
    
    def test_hg(self):
        basic = {
            'type': 'sovereign.service.base.Service',
            'src': 'hg:http://bitbucket.org/DeadWisdom/jsbundle'
        }
        self.node.create_service('basic', basic)
        self.assertFalse(self.node._get_service('basic').failed)
        self.node.delete_service('basic')
    
    def test_git(self):
        basic = {
            'type': 'sovereign.service.base.Service',
            'src': 'git://github.com/DeadWisdom/Vanilla.git'
        }
        self.node.create_service('basic', basic)
        self.assertFalse(self.node._get_service('basic').failed)
        self.node.delete_service('basic')
    
    def test_svn(self):
        basic = {
            'type': 'sovereign.service.base.Service',
            'src': 'svn:http://jquery-json.googlecode.com/svn/trunk/'
        }
        self.node.create_service('basic', basic)
        self.assertFalse(self.node._get_service('basic').failed)
        self.node.delete_service('basic')
    
    def test_http_tar_gz(self):
        basic = {
            'type': 'sovereign.service.base.Service',
            'src': 'http://github.com/DeadWisdom/Vanilla/tarball/master'
        }
        self.node.create_service('basic', basic)
        self.assertFalse(self.node._get_service('basic').failed)
        self.node.delete_service('basic')