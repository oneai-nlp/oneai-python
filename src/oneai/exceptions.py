import json
from aiohttp import ClientResponse

# todo: input type validation errors


class OneAIError(Exception):
    """
    A base class for all errors raised by the API.

    ## Attributes

    `status_code: int`
        The API status code of the error.
    `message: str`
        A human-readable message describing the error.
    `details: str`
        A string containing details about the error.
    """

    def __init__(self, status_code: int = 0, message: str = "", details: str = ""):
        self.status_code = status_code
        self.message = message
        self.details = details

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}("
            + (f", status_code={self.status_code}" if self.status_code else "")
            + (f", message={self.message}" if self.message else "")
            + (f", details={self.details})" if self.details else ")")
        )

    __repr__ = __str__


class InputError(OneAIError):
    """An error raised when the input is invalid or is of an incompatible type for the pipeline."""


class APIKeyError(OneAIError):
    """An error raised when the API key is invalid, expired, or missing quota."""


class ServerError(OneAIError):
    """An error raised when the an internal server error occured."""


errors = {  # map http status codes to OneAIError subclasses
    400: InputError,
    401: APIKeyError,
    403: APIKeyError,
    500: ServerError,
    503: ServerError,
}


async def handle_unsuccessful_response(response: ClientResponse):
    try:
        content = json.loads(await response.content.read())
    except:
        content = {}
    raise errors.get(response.status, ServerError)(
        content.get("status_code", response.status),
        content.get("message", response.reason),
        content.get("details", ""),
    )
