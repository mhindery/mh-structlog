import contextlib
import os
import pathlib

import filelock
import pytest
from django.conf import settings
from django.test.utils import setup_test_environment


@pytest.fixture(scope='session')
def lock(tmp_path_factory):
    base_temp = tmp_path_factory.getbasetemp()
    lock_file = base_temp.parent / 'serial.lock'
    yield filelock.FileLock(lock_file=str(lock_file))
    with contextlib.suppress(OSError):
        pathlib.Path(lock_file).unlink()


@pytest.fixture
def serial(lock):
    with lock.acquire(poll_intervall=0.1):
        yield


@pytest.fixture(scope='session')
def django_settings():
    settings.configure()
    setup_test_environment(debug=True)
