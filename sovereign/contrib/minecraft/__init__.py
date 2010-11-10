from sovereign.service import ProcessService, StringField

class Service(ProcessService):
    name = "minecraft"
    
    settings = [
        StringField('executable', 'java'),
        StringField('args', ['-cp', 'minecraft-server.jar', 'com.mojang.minecraft.server.MinecraftServer']),
        StringField('src', 'http://www.minecraft.net/minecraft-server.zip'),
    ]