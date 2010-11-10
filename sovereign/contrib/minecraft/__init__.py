from sovereign.service import ProcessService, StringField

class Service(ProcessService):
    name = "minecraft"
    
    settings = [
        StringField('executable', 'java'),
        StringField('args', ['-Xmx1024M', '-Xms1024M', '-jar', 'minecraft_server.jar', 'nogui']),
        StringField('src', 'http://www.minecraft.net/download/minecraft_server.jar'),
    ]