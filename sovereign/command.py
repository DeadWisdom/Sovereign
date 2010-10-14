#!env/bin/python
import argparse
import eventlet

from node import LocalNode

def run():
    parser = get_parser()
    options = parser.parse_args()
    
    node = LocalNode(options.repository)
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
    
    return parser

if __name__ == '__main__':
    server()