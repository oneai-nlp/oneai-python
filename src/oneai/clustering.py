from dataclasses import dataclass, field
from datetime import datetime
import urllib.parse
from typing import Generator, List, Union
from typing_extensions import Literal
import oneai
from oneai.api import get_clustering, get_clustering_paginated, post_clustering
from oneai.classes import Input, PipelineInput

API_DATE_FORMAT = "%Y-%m-%d"


def get_collections(
    api_key: str = None,
    *,
    limit: int = None,
) -> Generator["Collection", None, None]:
    yield from get_clustering_paginated(
        "",
        api_key,
        "collections",
        None,
        from_dict=Collection,
        limit=limit,
    )


@dataclass
class Item(Input[str]):
    id: int
    text: str
    datetime: datetime
    distance: float
    phrase: "Phrase" = field(repr=False)
    cluster: "Cluster" = field(repr=False)
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, phrase: "Phrase", object: dict) -> "Item":
        item = cls(
            id=object["id"],
            text=object["original_text"],
            datetime=datetime.strptime(object["create_date"], f"%Y-%m-%d %H:%M:%S.%f"),
            distance=object["distance_to_phrase"],
            phrase=phrase,
            cluster=phrase.cluster,
            metadata={k: v[0]["value"] for k, v in object["metadata"].items()},
        )
        item.type = "article"
        item.content_type = "text/plain"
        return item


@dataclass
class Phrase:
    id: int
    text: str
    item_count: int
    cluster: "Cluster" = field(repr=False)
    collection: "Collection" = field(repr=False)
    metadata: dict = field(default_factory=dict)

    def get_items(
        self,
        *,
        limit: int = None,
        item_metadata: str = None,
    ) -> List[Item]:
        yield from get_clustering_paginated(
            f"{self.collection.id}/phrases/{self.id}/items",
            self.collection.api_key,
            "items",
            self,
            Item.from_dict,
            limit=limit,
            item_metadata=item_metadata,
        )

    @classmethod
    def from_dict(cls, cluster: "Cluster", object: dict) -> "Phrase":
        return cls(
            id=int(object["phrase_id"]),
            text=object.get("text", ""),
            item_count=object["items_count"],
            cluster=cluster,
            collection=cluster.collection,
            metadata=object["metadata"],
        )


@dataclass
class Cluster:
    id: int
    text: str
    phrase_count: int
    item_count: int
    collection: "Collection" = field(repr=False)
    metadata: dict = field(default_factory=dict)

    def get_phrases(
        self,
        *,
        sort: Literal["ASC", "DESC"] = "ASC",
        limit: int = None,
        from_date: Union[datetime, str] = None,
        to_date: Union[datetime, str] = None,
        date_format: str = API_DATE_FORMAT,
        item_metadata: str = None,
    ) -> Generator[Phrase, None, None]:
        yield from get_clustering_paginated(
            f"{self.collection.id}/clusters/{self.id}/phrases",
            self.collection.api_key,
            "phrases",
            self,
            Phrase.from_dict,
            sort,
            limit,
            from_date,
            to_date,
            date_format,
            item_metadata,
        )

    def get_items(
        self,
        *,
        sort: Literal["ASC", "DESC"] = "ASC",
        limit: int = None,
        from_date: Union[datetime, str] = None,
        to_date: Union[datetime, str] = None,
        date_format: str = API_DATE_FORMAT,
        item_metadata: str = None,
    ) -> Generator[Phrase, None, None]:
        yield from get_clustering_paginated(
            f"{self.collection.id}/clusters/{self.id}/items",
            self.collection.api_key,
            "items",
            self,
            Item.from_dict,
            sort,
            limit,
            from_date,
            to_date,
            date_format,
            item_metadata,
        )

    def add_items(self, items: List[PipelineInput[str]]):
        url = f"{self.collection.id}/items"
        data = [
            {
                "text": item.text if isinstance(item, Input) else item,
                "item_metadata": item.metadata if isinstance(item, Input) else None,
                "force-cluster-id": self.id,
            }
            for item in items
        ]
        post_clustering(url, data, self.collection.api_key)

    @classmethod
    def from_dict(cls, collection: "Collection", object: dict) -> "Cluster":
        return cls(
            id=int(object["cluster_id"]),
            text=object["cluster_phrase"],
            phrase_count=object["phrases_count"],
            item_count=object["items_count"],
            collection=collection,
            metadata=object["metadata"],
        )


class Collection:
    def __init__(self, id: str, api_key: str = None):
        self.id = id
        self.api_key = api_key or oneai.api_key

    def get_clusters(
        self,
        *,
        sort: Literal["ASC", "DESC"] = "ASC",
        limit: int = None,
        from_date: Union[datetime, str] = None,
        to_date: Union[datetime, str] = None,
        date_format: str = API_DATE_FORMAT,
        item_metadata: str = None,
    ) -> Generator[Cluster, None, None]:
        yield from get_clustering_paginated(
            f"{self.id}/clusters",
            self.api_key,
            "clusters",
            self,
            Cluster.from_dict,
            sort,
            limit,
            from_date,
            to_date,
            date_format,
            item_metadata,
        )

    def find(self, query: str, threshold: float = 0.5) -> List[Cluster]:
        params = {
            "text": query,
            "similarity-threshold": threshold,
        }

        url = f"{self.id}/clusters/find?{urllib.parse.urlencode(params)}"
        return [
            Cluster.from_dict(self, cluster)
            for cluster in get_clustering(url, self.api_key)
        ]

    def add_items(
        self, items: List[PipelineInput[str]], force_new_clusters: bool = False
    ):
        def build_item(input: PipelineInput[str]):
            result = {
                "text": input.text if isinstance(input, Input) else str(input),
                "force-new-cluster": force_new_clusters,
            }
            if hasattr(input, "metadata") and input.metadata:
                result["item_metadata"] = input.metadata
            if hasattr(input, "datetime") and input.datetime:
                result["timestamp"] = int(input.datetime.timestamp())
            return result

        url = f"{self.id}/items"
        data = [build_item(item) for item in items]
        print(post_clustering(url, data, self.api_key))

    def __repr__(self) -> str:
        return f"oneai.Collection({self.id})"
