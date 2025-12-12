import structlog
from aws_lambda_powertools.utilities.typing import LambdaContext


def bind_lambda_context(lambda_context: LambdaContext) -> None:
    """Bind AWS Lambda context information to the structlog context variables, so log entries contain Lambda function metadata.

    Args:
        lambda_context (LambdaContext): The AWS Lambda context object.
    """
    if lambda_context:
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            function_name=lambda_context.function_name,
            function_memory_size=lambda_context.memory_limit_in_mb,
            function_arn=lambda_context.invoked_function_arn,
            function_request_id=lambda_context.aws_request_id,
        )
