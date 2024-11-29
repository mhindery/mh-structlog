# MH-Structlog

This package is used to setup the python logging system in combination with structlog. It configures both structlog and the standard library logging module, so your code can either use a structlog logger (which is recommended) or keep working with the standard logging library. This way all third-party packages that are producing logs (which use the stdlib logging module) will follow your logging setup and you will always output structured logging.

It is a fairly opinionated setup but has some configuration options to influence the behaviour. The two output log formats are either pretty-printing (for interactive views) or json. It includes optional reporting to Sentry, and can also log to a file.

## Usage

This library should behave mostly as a drop-in import instead of the logging library import.

So instead of

```python
import logging

logger = logging.getLogger(__name__)

logger.info('hey')
```

you can do

```python
import mh_structlog as logging
logging.setup()  # necessary once at program startup, see readme further below

logger = logging.getLogger(__name__)

logger.info('hey')
```

One big advantage of using the structlog logger over de stdlib logging one, is that you can pass arbitrary keyword arguments to our loggers when producing logs. E.g.

```python
import mh_structlog as logging

logger = logging.getLogger(__name__)

logger.info('some message', hey='ho', a_list=[1,2,3])
```

These extra key-value pairs will be included in the produced logs; either pretty-printed to the console or as data in the json entries.

## Configuration via `setup()`

To configure your logging, call the `setup` function, which should be called once as early as possible in your program execution. This function configures all loggers.

```python
import mh_structlog as logging

logging.setup()
```

This will work out of the box with sane defaults: it logs to stdout in a pretty colored output when running in an interactive terminal, else it defaults to producing json output. See the next section for information on the arguments to this method.

### Configuration options

For a setup which logs everything to the console in a pretty (colored) output, simply do:

```python
from mh_structlog import *

setup(
    log_format='console',
)

getLogger().info('hey')
```

To log as json:

```python
from mh_structlog import *

setup(
    log_format='json',
)

getLogger().info('hey')
```

To filter everything out up to a certain level:

```python
from mh_structlog import *

setup(
    log_format='console',
    global_filter_level=WARNING,
)

getLogger().info('hey')  # this does not get printed
getLogger().error('hey')  # this does get printed
```

To write logs to a file additionally (next to stdout):

```python
from mh_structlog import *

setup(
    log_format='console',
    log_file='myfile.log',
)

getLogger().info('hey')
```

To silence specific named loggers specifically (instead of setting the log level globally, it can be done per named logger):

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

To include the source information about where a log was produced:

```python
from mh_structlog import *

setup(
    include_source_location=True
)

getLogger().info('hey')
```

To choose how many frames you want to include in stacktraces on logging exceptions:

```python
from mh_structlog import *

setup(
    log_format='json',
    max_frames=3,
)

try:
    5 / 0
except Exception as e:
    getLogger().exception(e)
```

To enable Sentry integration, pass a dict with a config according to the arguments which [structlog-sentry](https://github.com/kiwicom/structlog-sentry?tab=readme-ov-file#usage) allows to the setup function:

```python
from mh_structlog import *
import sentry_sdk

config = {'dsn': '1234'}
sentry_sdk.init(dsn=config['dsn'])

setup(
    sentry_config={'event_level': WARNING}  # pass everything starting from WARNING level to Sentry
)

```
