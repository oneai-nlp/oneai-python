from oneai.api.pipeline import post_pipeline
from oneai.api.clustering import (
    post_clustering,
    get_clustering,
    get_clustering_paginated,
)


def get_or_create_uuid() -> str:
    import os, uuid

    with open(f"{os.path.dirname(__file__)}/.uuid", "a+") as f:
        f.seek(0)
        id = f.read()
        if not id:
            id = uuid.uuid4().hex
            f.write(id)
        return id


uuid = get_or_create_uuid()
