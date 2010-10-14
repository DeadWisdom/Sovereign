import platform
system = platform.system()
distro = platform.dist()[0]

if (system == 'Darwin'):
    import osx
    mod = osx
elif (system == 'Linux'):
    if (distro in ('debian', 'ubuntu')):
        import debian
        mod = debian
    else:
        raise NotImplementedError("Your linux distribution is not supported by sovereign.")
else:
    raise NotImplementedError("Your system is not supported by sovereign.")

for k in ['sys_install', 'sys_uninstall', 'sys_upgrade']:
    globals()[k] = getattr(mod, k)
