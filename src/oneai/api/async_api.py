import aiohttp
import asyncio
import oneai, oneai.api

from oneai.exceptions import handle_unsuccessful_response, validate_api_key

endpoint_async_tasks = 'api/v0/pipeline/async/tasks'

STATUS_COMPLETED = 'COMPLETED'
STATUS_FAILED = 'FAILED'

async def monitor_task(
    session: aiohttp.ClientSession,
    task_id: str,
    api_key: str,
    poll_interval: int = 1,
):
    validate_api_key(api_key)

    url = f"{oneai.URL}/{endpoint_async_tasks}/{task_id}"
    headers = {
        "api-key": api_key,
        "User-Agent": f"python-sdk/{oneai.__version__}/{oneai.api.uuid}",
    }

    status = ''
    body = {}
    while status != STATUS_COMPLETED:
        if status == STATUS_FAILED:
            # todo: fix this
            await handle_unsuccessful_response(body)

        async with session.get(url, headers=headers) as response:
            print(f'made request {body=}')
            if response.status != 200:
                await handle_unsuccessful_response(response)
            else:
                body = await response.json()
                status = body['status']
        await asyncio.sleep(poll_interval)
    return body
