#!/usr/bin/python
import os, sys, logging, shutil
from unittest import TestCase

import eventlet
from eventlet.green import httplib
from sovereign.node import LocalNode
from sovereign.service.base import Service as BaseService

class TestWeb(TestCase):
    WEB_FRONT = ('127.0.0.1', 7892)        # randomly decided, hope it works.
    WEB_BACK = ('127.0.0.1', 7893)
    
    def _request(self, url, method='GET', body=None, headers=None):
        conn = httplib.HTTPConnection(self.WEB_FRONT[0], self.WEB_FRONT[1], url)
        conn.request(method, url, body, headers or {})
        return conn.getresponse()
    
    def setUp(self):
        self._path = os.path.join(os.path.dirname(__file__), 'web')
        if (os.path.exists(self._path)):
            shutil.rmtree(self._path)
        
        self.node = LocalNode(path=self._path, id='node-a')
        self._server = eventlet.spawn(self.node.serve, ('127.0.0.1', 1648))
        eventlet.sleep(0)
    
    def tearDown(self):
        self._server.kill()
        eventlet.sleep(0)
        if (os.path.exists(self._path)):
            shutil.rmtree(self._path)
    
    def test_web_service(self):
        web = { 
            'type': 'sovereign.contrib.web.Service', 
            'id': 'web-front', 
            'address': self.WEB_FRONT,
            'motd': 'Greetings',
        }
        service = self.node.create_service('web', web)
        
        response = self._request('/')
        self.assertEqual(response.status, 200)
        
        response = self._request('/asdf')
        self.assertEqual(response.status, 404)
        
        self.node.delete_service(service['id'])

    def test_web_proxy(self):
        services = [
            { 
              'type': 'sovereign.contrib.web.Service', 
              'id': 'web-front', 
              'address': self.WEB_FRONT,
            },
            { 
              'type': 'sovereign.contrib.web.Service', 
              'id': 'web-back', 
              'address': self.WEB_BACK,
              'motd': 'Greetings' 
            },
        ]
        
        for service in services:
            self.node.create_service(service['id'], service)
        
        response = self._request('/')
        self.assertEqual(response.status, 404)
        
        self.node.msg_service('web-front', 'proxy', address=self.WEB_BACK)
        
        response = self._request('/')
        self.assertEqual(response.status, 200)
        
        for service in services:
            self.node.delete_service(service['id'])
        
        self.assertEqual(len(self.node.services), 1)  #Because admin will be there.