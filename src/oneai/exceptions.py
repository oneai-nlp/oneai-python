from aiohttp import ClientResponse

# todo: input type validation errors


class InputError(Exception):
    pass

class APIKeyError(Exception):
    pass

class ServerError(Exception):
    pass

# todo: fix this
errors = {
    400: InputError,
    401: APIKeyError,
    403: APIKeyError,
    500: ServerError,
    503: ServerError
}

def handle_unsuccessful_response(response: ClientResponse):
    raise errors.get(response.status, ServerError)(response.reason)
