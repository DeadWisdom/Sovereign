from sovereign.util import shell

def sys_install(packages):
    raise NotImplementedError("OSX does not support package installation.")

def sys_upgrade(packages):
    raise NotImplementedError("OSX does not support package upgrading.")

def sys_uninstall(packages):
    raise NotImplementedError("OSX does not support package removal.")