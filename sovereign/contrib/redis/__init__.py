from sovereign.service import ProcessService, StringField

class Service(ProcessService):
    name = "redis"
    
    settings = [
        StringField('executable', 'src/redis-server'),
        StringField('src', 'git:http://github.com/antirez/redis.git'),
    ]
    
    def deploy_msg(self):
        self.command("make")