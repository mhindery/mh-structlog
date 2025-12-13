from collections.abc import Generator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO
from typing import TextIO


@contextmanager
def capture_output() -> Generator[tuple[TextIO, TextIO]]:
    """
    Capture both stdout and stderr into StringIO buffers.

    Source: https://adamj.eu/tech/2025/08/29/python-unittest-capture-stdout-stderr/
    """
    with redirect_stdout(StringIO()) as out, redirect_stderr(StringIO()) as err:
        yield out, err
