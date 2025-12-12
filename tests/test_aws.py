from unittest.mock import Mock

from aws_lambda_powertools.utilities.typing import LambdaContext
from structlog.contextvars import clear_contextvars, get_contextvars

from mh_structlog.aws import bind_lambda_context


def test_bind_lambda_context_non_empty():
    clear_contextvars()

    mock_lambda_context = Mock(spec=LambdaContext)
    mock_lambda_context.function_name = "test_function"
    mock_lambda_context.memory_limit_in_mb = 128
    mock_lambda_context.invoked_function_arn = "arn:aws:lambda:region:account-id:function:test_function"
    mock_lambda_context.aws_request_id = "1234-5678"

    assert get_contextvars() == {}

    bind_lambda_context(mock_lambda_context)

    assert get_contextvars() == {
        'function_arn': 'arn:aws:lambda:region:account-id:function:test_function',
        'function_memory_size': 128,
        'function_name': 'test_function',
        'function_request_id': '1234-5678',
    }


def test_bind_lambda_context_empty():
    clear_contextvars()

    assert get_contextvars() == {}

    bind_lambda_context(None)

    assert get_contextvars() == {}
