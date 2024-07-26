import inspect


def determine_name_for_logger():
    """Return a name for a logger depending on the stackframe."""
    frame = inspect.stack()[-1]

    # Make a name ourselves
    name: str = frame[1].lstrip('/').rstrip('.py').replace('/', '.')

    # Strip away some common 'prefixes' paths
    for location in ['src', 'code', 'app']:
        if f'{location}.' in name:
            _, _, name = name.partition(f'{location}.')
            break

    return name
