from datetime import datetime
import json
import requests
import urllib.parse
from typing import Union, Callable, Any
from typing_extensions import Literal
import oneai, oneai.api


API_DATE_FORMAT = "%Y-%m-%d"

ENDPOINT = "clustering/v1/collections"


def build_query_params(
    sort: Literal["ASC", "DESC"] = None,
    limit: int = None,
    from_date: Union[datetime, str] = None,
    to_date: Union[datetime, str] = None,
    date_format: str = API_DATE_FORMAT,
    item_metadata: str = None,
):
    if from_date:
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date, date_format)
        from_date = from_date.strftime(API_DATE_FORMAT)

    if to_date:
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date, date_format)
        to_date = to_date.strftime(API_DATE_FORMAT)

    params = {
        "sort": sort,
        "limit": limit if limit else 20,
        "from-date": from_date,
        "to-date": to_date,
        "include-phrases": False,
        "item-metadata": item_metadata,
    }
    return urllib.parse.urlencode({k: v for k, v in params.items() if v})


def get_clustering_paginated(
    path: str,
    api_key: str,
    result_key: str,
    parent: Any,
    from_dict: Callable[[Any, dict], Any],
    sort: Literal["ASC", "DESC"] = None,
    limit: int = None,
    from_date: Union[datetime, str] = None,
    to_date: Union[datetime, str] = None,
    date_format: str = API_DATE_FORMAT,
    item_metadata: str = None,
):
    path_query = f"{path}?{build_query_params(sort, limit, from_date, to_date, date_format, item_metadata)}"
    page = 0
    counter = 0
    results = [None]

    while results and ((not limit) or counter < limit):
        response = get_clustering(f"{path_query}&page={page}", api_key)
        results = [
            (from_dict(parent, result) if parent else from_dict(result))
            for result in response[result_key]
        ]
        yield from results
        counter += len(results)
        page += 1

        if page >= response.get("total_pages", 0):
            break


def get_clustering(path: str, api_key: str = None):
    api_key = api_key or oneai.api_key
    if not api_key:
        raise Exception("API key is required")
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "User-Agent": f"python-sdk/{oneai.__version__}/{oneai.api.uuid}",
    }
    if oneai.DEBUG_LOG_REQUESTS:
        oneai.logger.debug(f"GET {oneai.URL}/{ENDPOINT}/{path}\n")
        oneai.logger.debug(f"headers={json.dumps(headers, indent=4)}\n")
    response = requests.get(
        f"{oneai.URL}/{ENDPOINT}/{path}",
        headers=headers,
    )
    return json.loads(response.content)


def post_clustering(path: str, data: dict, api_key: str = None):
    api_key = api_key or oneai.api_key
    if not api_key:
        raise Exception("API key is required")
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "User-Agent": f"python-sdk/{oneai.__version__}/{oneai.api.uuid}",
    }
    if oneai.DEBUG_LOG_REQUESTS:
        oneai.logger.debug(f"POST {oneai.URL}/{ENDPOINT}/{path}\n")
        oneai.logger.debug(f"headers={json.dumps(headers, indent=4)}\n")
        oneai.logger.debug(f"data={json.dumps(data, indent=4)}\n")
    response = requests.post(
        f"{oneai.URL}/{ENDPOINT}/{path}", headers=headers, json=data
    )
    return json.loads(response.content)
