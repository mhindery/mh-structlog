# Structlog logging

Setup the python logging system using structlog. This module configures both structlog and the standard library logging module. So your code can either use a structlog logger or keep working with the standard logging library. This way all third-party packages that you use, which use the stdlib logging module, will follow your logging setup for e.g. structured logging in json.

## Import

This library should behave mostly as a drop-in import instead of the logging library import.

So instead of 

```python
import logging

logging.getLogger().info('hey)
```

you can do

```python
import mh_structlog as logging

logging.getLogger().info('hey)
```

## Usage

The main function of this package is the `setup` function which should be called once as early as possible in your code. This function configures the loggers.

```python
import mh_structlog as logging

logging.setup()
```

This will work out of the box with sane defaults: it logs to stdout in a pretty colored output. See the section below for options to this method.

## Setup options

For a setup which logs everything to the console in a pretty (colored) output, simply do:

```python
from mh_structlog import *

setup(
    log_format='console',
)

getLogger('some_named_logger').info('hey')
```

To log as json:

```python
from mh_structlog import *

setup(
    log_format='json',
)

getLogger('some_named_logger').info('hey')
```

To filter everything to a certain level:

```python
from mh_structlog import *

setup(
    log_format='console',
    global_filter_level=WARNING,
)

getLogger('some_named_logger').info('hey')  # this does not get printed
getLogger('some_named_logger').error('hey')  # this does get printed
```

To write to a file additionally, next to stdout:

```python
from mh_structlog import *

setup(
    log_format='console',
    log_file='myfile.log',
)

getLogger('some_named_logger').info('hey')
```

To silence one named logger specifically (instead of setting the log level globally):

```python
from mh_structlog import *

setup(
    log_format='console',
    logging_configs=[
        filter_named_logger('some_named_logger', WARNING),
    ],
)

getLogger('some_named_logger').info('hey')  # does not get logged
getLogger('some_named_logger').warning('hey')  # does get logged

getLogger('some_other_named_logger').info('hey')  # does get logged
getLogger('some_other_named_logger').warning('hey')  # does get logged
```