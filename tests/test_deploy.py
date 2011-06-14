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
        self.node.nanny()
    
    def tearDown(self):
        self.node.terminate()
        self._server.kill()
        eventlet.sleep(0)
        for p in self.paths:
            try:
                shutil.rmtree(os.path.join(os.path.dirname(__file__), p))
            except:
                pass
    
    def _test_service(self, name, config):
        self.node.create_service(name, config)
        service = self.node._get_service(name)
        self.assertTrue(service.nanny())
        self.node.delete_service(name)
    
    def test_file_dir(self):
        name = "test_file_dir"
        config = {
            'type': 'sovereign.service.base.Service',
            'src': 'file:tests/src'
        }
        self._test_service(name, config)
        
    def test_file_tar_gz(self):
        name = "test_file_tar_gz"
        config = {
            'type': 'sovereign.service.base.Service',
            'src': 'file:tests/src.tar.gz'
        }
        self._test_service(name, config)
    
    def test_rsync(self):
        name = "test_rsync"
        config = {
            'type': 'sovereign.service.base.Service',
            'src': 'rsync:tests/src'
        }
        self._test_service(name, config)
    
    def test_hg(self):
        name = "test_hg"
        config = {
            'type': 'sovereign.service.base.Service',
            'src': 'hg:http://bitbucket.org/DeadWisdom/jsbundle'
        }
        self._test_service(name, config)
    
    def test_git(self):
        name = "test_git"
        config = {
            'type': 'sovereign.service.base.Service',
            'src': 'git://github.com/DeadWisdom/Vanilla.git'
        }
        self._test_service(name, config)
    
    def test_svn(self):
        name = "test_svn"
        config = {
            'type': 'sovereign.service.base.Service',
            'src': 'svn:http://jquery-json.googlecode.com/svn/trunk/'
        }
        self._test_service(name, config)
    
    def test_http_tar_gz(self):
        name = "test_http_tar_gz"
        config = {
            'type': 'sovereign.service.base.Service',
            'src': 'http://github.com/DeadWisdom/Vanilla/tarball/master'
        }
        self._test_service(name, config)