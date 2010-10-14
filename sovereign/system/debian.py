from sovereign.util import shell

def sys_install(packages):
    return shell('apt-get install %s' % " ".join(packages))

def sys_upgrade(packages):
    return shell('apt-get upgrade %s' % " ".join(packages))

def sys_uninstall(packages):
    return shell('apt-get remove %s' % " ".join(packages))
    