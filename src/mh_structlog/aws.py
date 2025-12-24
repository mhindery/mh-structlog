import os

import structlog
from aws_lambda_powertools.utilities.typing import LambdaContext


is_cold_start = True


def _reset_cold_start_flag() -> None:
    """Reset the cold start flag to True. This is primarily intended for testing purposes."""
    global is_cold_start  # noqa: PLW0603
    is_cold_start = True


def bind_lambda_context(lambda_context: LambdaContext) -> None:
    """Bind AWS Lambda context information to the structlog context variables, so log entries contain Lambda function metadata.

    Args:
        lambda_context (LambdaContext): The AWS Lambda context object.
    """
    global is_cold_start  # noqa: PLW0603

    if lambda_context:
        structlog.contextvars.clear_contextvars()

        if os.getenv('AWS_LAMBDA_INITIALIZATION_TYPE', '') == "provisioned-concurrency":
            is_cold_start = False

        structlog.contextvars.bind_contextvars(
            function_name=lambda_context.function_name,
            function_memory_size=lambda_context.memory_limit_in_mb,
            function_arn=lambda_context.invoked_function_arn,
            function_request_id=lambda_context.aws_request_id,
            cold_start=is_cold_start,
        )

        # After the first invocation of an environment, set cold_start to False for further invocations
        is_cold_start = False
