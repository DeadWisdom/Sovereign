
# This get's around an import problem.
def run(*a, **ka):
    from command import run
    run(*a, **ka)