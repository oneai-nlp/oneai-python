from dataclasses import dataclass, field, asdict
from datetime import datetime
from dateutil import parser as dateutil
import urllib.parse
from typing import Generator, List, Optional, Union
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
    text_index: Optional[str] = None

    @classmethod
    def from_dict(cls, phrase: "Phrase", object: dict) -> "Item":
        item = cls(
            id=object.get("id", object.get("item_id", None)),
            text=object.get("original_text", object.get("item_original_text")),
            datetime=dateutil.parse(object["create_date"])
            if isinstance(object["create_date"], str)
            else datetime.fromtimestamp(object["create_date"] / 1000),
            distance=object["distance_to_phrase"],
            phrase=phrase if isinstance(phrase, Phrase) else None,
            cluster=phrase.cluster if isinstance(phrase, Phrase) else phrase,
            metadata=object.get("metadata", {}),
            text_index=object.get(
                "translated_text", object.get("item_translated_text", None)
            ),
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
    text_index: Optional[str] = None
    _items: Optional[List[Item]] = None

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
    def from_dict(
        cls, cluster: "Cluster", object: dict, collection: "Collection" = None
    ) -> "Phrase":
        phrase = cls(
            id=int(object["phrase_id"]),
            text=object.get("text", object.get("phrase_text", "")),
            item_count=object["items_count"],
            cluster=cluster,
            collection=cluster.collection if cluster else collection,
            metadata=object.get("metadata", None),
            text_index=object.get("item_translated_text", None),
        )
        phrase._items = [
            Item.from_dict(phrase, item) for item in object.get("items", [])
        ]
        return phrase


@dataclass
class Cluster:
    id: int
    text: str
    phrase_count: int
    item_count: int
    collection: "Collection" = field(repr=False)
    metadata: dict = field(default_factory=dict)
    text_index: Optional[str] = None

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
            None,
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
            text=object["cluster_phrase"]
            if "cluster_phrase" in object
            else object["cluster_text"],
            phrase_count=object.get("phrases_count", -1),
            item_count=object.get("items_count", -1),
            collection=collection,
            metadata=object.get("metadata", None),
            text_index=object.get("item_translated_text", None),
        )


@dataclass
class AccessSettings:
    query: bool = True
    list_clusters: bool = True
    list_phrases: bool = True
    list_items: bool = True
    add_items: bool = True
    edit_clusters: bool = True
    discoverable: bool = True


class Collection:
    def __init__(
        self,
        id: str,
        api_key: str = None,
    ):
        self.id = id
        self.api_key = api_key or oneai.api_key

    @classmethod
    def create(
        cls,
        id: str,
        *,
        api_key: str = None,
        access: AccessSettings = None,
        cluster_distance_threshold: float = None,
        phrase_distance_threshold: float = None,
        domain: Literal[
            "curation", "survey", "reviews", "service", "classify"
        ] = "service",
    ) -> "Collection":
        post_clustering(
            f"{id}/create",
            {
                "access": asdict(access if access else AccessSettings()),
                "cluster_distance_threshold": cluster_distance_threshold,
                "phrase_distance_threshold": phrase_distance_threshold,
                "domain": domain,
            },
        )
        return cls(id, api_key)

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

    def find_phrases(
        self,
        query: str,
        *,
        threshold: float = 0.5,
        limit: int = 100,
        include_items: bool = False,
        items_limit: int = 10,
        metadata_filter: str = None,
    ) -> List[Phrase]:
        params = {
            "text": query.replace("\n", "\\n"),
            "similarity-threshold": threshold,
            "max-phrases": limit,
            "include-items": include_items,
            "max-items": items_limit,
            "meta-query": metadata_filter,
        }

        url = f"{self.id}/phrases/find?{urllib.parse.urlencode(params)}"
        return [
            Phrase.from_dict(None, phrase, self)
            for phrase in get_clustering(url, self.api_key)
        ]

    def find_clusters(self, query: str, threshold: float = 0.5) -> List[Cluster]:
        params = {
            "text": query.replace("\n", "\\n"),
            "similarity-threshold": threshold,
        }

        url = f"{self.id}/clusters/find?{urllib.parse.urlencode(params)}"
        return [
            Cluster.from_dict(self, cluster)
            for cluster in get_clustering(url, self.api_key)
        ]

    def add_items(
        self,
        items: List[PipelineInput[str]],
        *,
        cluster_distance_threshold: float = None,
        phrase_distance_threshold: float = None,
    ):
        def build_item(input: PipelineInput[str]):
            result = {
                "text": input.text if isinstance(input, Input) else str(input),
            }
            if cluster_distance_threshold:
                result["cluster_distance_threshold"] = cluster_distance_threshold
            if phrase_distance_threshold:
                result["phrase_distance_threshold"] = phrase_distance_threshold
            if hasattr(input, "metadata") and input.metadata:
                result["item_metadata"] = input.metadata
            if hasattr(input, "datetime") and input.datetime:
                result["timestamp"] = int(input.datetime.timestamp())
            if hasattr(input, "text_index") and input.text_index:
                result["input_translated"] = input.text_index
            return result

        url = f"{self.id}/items"
        data = [build_item(item) for item in items]
        return post_clustering(url, data, self.api_key)

    def __repr__(self) -> str:
        return f"oneai.Collection({self.id})"
