class NodeIdCollision(Exception):
    """
    Exception raised when trying to create a new node with an id of an
    already known node.
    """
    pass


class Node(object):
    """
        This is a base class / interface, and is not instantiated directly.
    
        A sovereign Node acts as the main interface, providing commands to
        move the gears of sovereign.
    """
    def __init__(self):
        raise NotImplementedError("Interface class, cannot be instantiated.")
    
    def sys_install(self, packages):
        """
            Installs the packages given, for instance, this would take:

                node.sys_install(['mysql', 'php'])
                
            And, on debian, would run:
                
                apt-get install mysql php
            
            This is not available in all environments, and only available
            if the user running the node has permission.
            
            returns <stdout>, <stderr>
        """
        raise NotImplementedError()
    
    def sys_uninsall(self, packages):
        """
            Uninstalls the packages, like sys_install() above.
            
            returns <stdout>, <stderr>
        """
        raise NotImplementedError()
    
    def pip_install(self, packages, env=None):
        """
            Installs the python packages given using pip, optionally to the
            given virtualenv *env*.
            
            Arguments given can be anything that you can pip install,
            including "-r /path/to/requirements.txt".
            
            returns <stdout>, <stderr> (supresses pip-log.txt)
        """
        raise NotImplementedError()
    
    def pip_uninstall(self, packages, env=None):
        """
            Uninstalls the python packages using pip.
            
            returns <stdout>, <stderr> (supresses pip-log.txt)
        """
        raise NotImplementedError()
    
    def sys(self, cmds):
        """
            Runs these commands in the system.
            
            returns <stdout>, <stderr>
        """
        raise NotImplementedError()
    
    def info(self):
        """
            Returns information and statistics from the server.
        """
        raise NotImplementedError()
    
    def create_service(self, id, settings):
        """
            Creates a new service with the given *id* and *settings*.
            
            If a service with the same *id* already exists ServiceIdCollision
            will be raised.
            
            Returns the new service.
            
            You can think of a service as a webserver, daemon application, or
            anything that can be begun and stopped.  A service can be
            identified as its local path, a remote repository (hg, git, svn),
            or a remote archive (.zip, .tar.gz)
        """
        raise NotImplementedError()
        
    def modify_service(self, id, settings):
        """
            Deletes the service with the *id*, if it exists, and then creates
            a new service with the given *id* and *settings*.
            
            Returns the new service.
        """
        raise NotImplementedError()
    
    def delete_service(self, id):
        """
            Deletes the service with the *id*, if it exists.
            
            Returns True
        """
        raise NotImplementedError()
    
    def get_service(self, id):
        """
            Returns the service with the given *id* if it exists, 
            otherwise None.
        """
        raise NotImplementedError()
    
    def get_service_log(self, id):
        """
            Returns the log for the service with the given *id* if it exists,
            otherwise None.
        """
        raise NotImplementedError()
    
    def msg_service(self, id, message, **kwargs):
        """
            Sends a *message* to the service *id*, with the given *kwargs*.
            Returns whatever the service returns.
            
            raises NameError, if the service does not accept that message.
        """
        raise NotImplementedError()
    
    def create_nodes(self, nodes):
        """
            Creates new nodes.  Nodes can be specified in different ways:
            
            Cloud tuples - sent to libcloud to create a new node:
                {'type': 'cloud',
                 'driver': <driver>,
                 'args': <arguments>}
                
                <driver>    - "rackspace", "linode", etc.
                <arguments> - A tuple of arguments like (user, api_key)
            
            Running server:
                {'type': 'ssh',
                 'address': [<host>, <port>],
                 'username': <username>,
                 'password': <password>,
                 'key': <key_file>,
                 'serve': [<host>, <port>]}
                 
                <address>      - address for the ssh connection
                <username>     - optional username for the ssh login
                <password>     - optional password for the ssh login
                <key>          - optional key_file path for the ssh login
                <host>, <port> - address to host the sovereign server on
                                 defaults to ['0.0.0.0', 1648]
            
            Local Node - runs a new local node:
                
                {'type': 'local',
                 'path': '/path/to/repo',
                 'serve': [<host>, <port>]}
                
                <path>         - the path for the repo
                <host>, <port> - address to host the sovereign server, no
                                 default, since this would run along-side
                                 the current node.
        """
        raise NotImplementedError()
    
    def identify_nodes(self, nodes):
        """
            Identifies the given nodes.
            
            If any of these nodes share the same master, or are the master,
            we will also identify the neighbors of those nodes, and so on.
        """
        raise NotImplementedError()
    
    def file_operations(self, operations):
        """
            Perform these file operations.  Operations is a list of tuples 
            in the form:
            [
                ('move', <src>, <dest>),
                ('sync', <src>, <dest>),
                ('copy', <src>, <dest>),
                ('remove', <src>),
                ...
            ]
            
            Where:
                'move', moves a file/folder from <src> to <dest>
                'copy', copy a file/folder from <src> to <dest>
                'sync', sync a file/folder <src> with <dest>
                'remove', removes the file/folder at <src>
        """
        raise NotImplementedError()
    
    def recognize(self, node):
        """Recognize target as the new sovereign master."""
        raise NotImplementedError()
    
    def terminate(self, recurse=True):
        """
            Terminate the node.
        
            If *recurse*, all vassals will also terminate.
        """
        raise NotImplementedError()

