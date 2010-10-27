#!env/bin/python
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
    node.serve(options.address)

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
    
    return parser

if __name__ == '__main__':
    server()