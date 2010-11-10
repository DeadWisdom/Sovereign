from sovereign.service import ProcessService, StringField

class Service(ProcessService):
    name = "redis"
    
    settings = [
        StringField('executable', 'src/redis-server'),
        #Setting('src', 'git:http://github.com/antirez/redis.git', str),
        StringField('src', 'git:/projects/redis'),
    ]
    
    def deploy_msg(self):
        self.command("make")