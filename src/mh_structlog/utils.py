import inspect
from pathlib import Path

import structlog


def determine_name_for_logger():
    """Return a name for a logger depending on the stackframe."""
    frames = inspect.stack()

    for f in frames:
        frame = f
        if 'mh_structlog' not in f[1]:
            break

    # Make a name ourselves based on the path in the stackframe
    name: str = frame[1].lstrip('/').rstrip('.py').replace('/', '.')

    # Strip away some common 'prefixes' paths
    cwd = str(Path.cwd()).lstrip('/').rstrip('.py').replace('/', '.')
    for location in [cwd, 'var.task', 'src', 'code', 'app']:
        name = name.removeprefix(f'{location}.')

    return name.strip('.')


def getLogger(name: str | None = None):  # noqa: ANN201, N802
    """Return a named logger."""
    if name is None:
        name = determine_name_for_logger()
    return structlog.get_logger(name)


def get_logger(name: str | None = None):  # noqa: ANN201
    """Return a named logger."""
    return getLogger(name)
