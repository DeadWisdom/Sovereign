#!env/bin/python
import os, pwd, grp
import argparse
import eventlet
import logging, logging.handlers

### Make the default logger go nowhere.
logger = logging.getLogger()
logger.addHandler(logging.handlers.BufferingHandler(0))


from node import LocalNode

def run():
    parser = get_parser()
    options = parser.parse_args()
    
    log_level = logging.WARNING
    if options.verbose:
        log_level = logging.INFO
    
    node = LocalNode(options.repository, log_level=log_level)
    
    if (options.user):
        set_process_owner(options.user)
        
    node.serve(options.address)


### Support ###
def set_process_owner(spec):
    user, _, group = spec.partition(":")
    if group:
        print "Changing to group: %s" % group
        os.setgid(grp.getgrnam(user).gr_gid)
    elif user:
        try:
            g_id = grp.getgrnam(user).gr_gid
            print "Changing to group: %s" % user
            os.setgid(g_id)
        except:
            pass
    if user:
        print "Changing to user: %s" % user
        os.setuid(pwd.getpwnam(user).pw_uid)
    return user, group


def socket(s):
    sock = str(s)
    if (':' not in s):
        return ('0.0.0.0', int(s))
    addr, _, port = s.partition(":")
    port = int(port)
    addr = str(addr)
    return (addr, port)

def get_parser():
    parser = argparse.ArgumentParser(description='Sovereign controls everything. This starts a local node.')
    
    default_user = None
    
    if os.geteuid() == 0:
        if 'SUDO_USER' in os.environ:
            default_user = os.environ['SUDO_USER']
    
    parser.add_argument('repository',
                        default=".",
                        help='The repository base path. Defaults to "."')
    
    parser.add_argument('-a',
                        dest="address",
                        type=socket,
                        help="Listen on the given ADDRESS, defaults to '0.0.0.0:1648'.",
                        metavar="ADDRESS",
                        default='0.0.0.0:1648')
                        
    parser.add_argument('-v', '--verbose',
                        dest="verbose",
                        action="store_true",
                        help="Output info logging messages to the console.",
                        default=False)
    
    parser.add_argument("-u", "--user", 
                        dest="user",
                        help="Run as USER[:GROUP] (defaults to 'minister:minister' if run by root, or if run with sudo the sudoing user)", 
                        metavar="USER", 
                        default=default_user)
    
    return parser

if __name__ == '__main__':
    server()