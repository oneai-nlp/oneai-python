import json
from aiohttp import ClientResponse

# todo: input type validation errors

class OneAIError(Exception):
    def __init__(self, status_code: int, message: str='', details: str=''):
        self.status_code = status_code
        self.message = message
        self.details = details

    def __str__(self) -> str:
        return f'{type(self).__name__}(status_code={self.status_code}' \
            + (f', message={self.message}' if self.message else '') \
            + (f', details={self.details})' if self.details else ')')

    __repr__ = __str__

class InputError(OneAIError):
    pass

class APIKeyError(OneAIError):
    pass

class ServerError(OneAIError):
    pass

errors = {
    400: InputError,
    401: APIKeyError,
    403: APIKeyError,
    500: ServerError,
    503: ServerError
}

async def handle_unsuccessful_response(response: ClientResponse):
    try:
        content = json.loads(await response.content.read())
    except:
        content = {}
    raise errors.get(response.status, ServerError)(
        content.get('status_code', response.status),
        content.get('message', response.reason),
        content.get('details', '')
    )
