import os, time
from sovereign import http, service, template, util, static
from eventlet.wsgi import format_date_time

MEDIA_PATH = os.path.abspath(
    os.path.join( os.path.dirname(__file__), 'media' )
)

class Service(service.Service):
    name = "admin"
    
    def init(self):
        self._index = util.MutableFile( os.path.join(MEDIA_PATH, 'index.html') )
        self._media = static.Static( root = MEDIA_PATH, volatile = True )
    
    def route(self, env):
        if (env['PATH_INFO'] == '/'):
            return self.index(env)
        if (env['PATH_INFO'].startswith('/media')):
            util.eat_path_info(env, '/media')
            return self._media
    
    def index(self, env):
        self.logger.info("ACCESS - %s - %s" % ( env['REMOTE_ADDR'], log_date_time_string() )) 
        content = template.simple_template(self._index.read(), {
            'url': env['PATH_INFO'],
            'title': 'Administration',
            'msg': 'We are sovereign',
            'service_types': util.json.dumps(self.get_service_types())
        })
        return http.Response(content=content)
    
    def get_service_types(self):
        types = {}
        for name, cls in service.Service.classes.items():
            types[name] = {
                'type': name,
                'fields': [self.get_service_field(x) for x in cls.settings]
            }
        return tuple( types[k] for k in sorted(types.keys()) )
    
    def get_service_field(self, field):
        return {
            'type': field.__class__.__name__,
            'default': field.get_simple(field.default),
            'help': field.help,
            'label': field.key,
            'name': field.key
        }


### Utilities ###
monthname = [None,
             'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
             
def log_date_time_string():
    """Return the current time formatted for logging."""
    now = time.time()
    year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
    s = "%02d/%3s/%04d %02d:%02d:%02d" % (day, monthname[month], year, hh, mm, ss)
    return s