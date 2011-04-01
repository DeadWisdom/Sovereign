#!/usr/bin/python
from unittest import TestCase

from sovereign.service.settings import *

class TestSettings(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_basic(self):
        s = Settings()
        
        settings1 = [
            IdField('id', None),
            NoteField('description', ''),
            BoolField('disabled', False),
            StringList('deploy', [], "Commands to execute at the end of deployment."),
        ]
        
        settings2 = [
            BoolField('disabled', True),
            NoteField('memo', 'memo_town'),
        ]
        
        s.add(Fieldset('settings1', settings1))
        
        assert len(s.fieldsets) == 1
        assert s.defaults() == {
            'id': None,
            'description': '',
            'disabled': False,
            'deploy': []
        }
        
        s.add(Fieldset('settings2', settings2))
        
        assert len(s.fieldsets) == 2
        assert s.defaults() == {
            'id': None,
            'description': '',
            'disabled': True,
            'deploy': [],
            'memo': 'memo_town'
        }