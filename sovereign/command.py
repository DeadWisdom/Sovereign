#!env/bin/python
import os, pwd, grp
import argparse
import eventlet
import logging, logging.handlers

### Make the default logger go nowhere.
logger = logging.getLogger()
logger.addHandler(logging.handlers.BufferingHandler(0))

from baron import Baron
from node import LocalNode


def run():
    parser = get_parser()
    options = parser.parse_args()
    
    log_level = logging.WARNING
    if options.verbose:
        log_level = logging.DEBUG
    
    baron = Baron()

    if options.start or options.stop or options.restart:
        pid_file = os.path.join(options.repository, "daemon.pid")
        baron.ensure_pid_path(pid_file, options.user or "")
        if options.restart:
            baron.stop_daemon(pid_file)
        
        if options.stop:
            baron.stop_daemon(pid_file)
            return
        
        pid = baron.start_daemon(pid_file, working_dir=options.repository)
    
    if os.geteuid() == 0:
        baron.fork()
    
    if options.user:
        baron.set_owner(options.user)
        
    node = LocalNode(options.repository, log_level=log_level, baron=baron, address=options.address)
    
    node.serve()


### Support ###
def address(s):
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
                        type=address,
                        help="Listen on the given ADDRESS, defaults to '0.0.0.0:1648'.",
                        metavar="ADDRESS",
                        default=None)
                        
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
    
    group = parser.add_mutually_exclusive_group()
    
    group.add_argument("--start",
                        dest="start",
                        action="store_true",
                        help="Start as a daemon.",
                        default=False)
    
    group.add_argument("--restart",
                        dest="restart",
                        action="store_true",
                        help="Restart the existing daemon process.",
                        default=False)
                        
    group.add_argument("--stop",
                        dest="stop",
                        action="store_true",
                        help="Stop the existing daemon process.",
                        default=False)
    
    return parser

if __name__ == '__main__':
    server()