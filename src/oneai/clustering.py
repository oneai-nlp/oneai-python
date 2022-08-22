from dataclasses import dataclass, field
from datetime import datetime
import json
import urllib.parse
from typing import Generator, List, Literal, Union
import oneai
from oneai.api import get_clustering, post_clustering
from oneai.classes import Input


def get_collections(
    api_key: str = None,
    limit: int = None,
) -> Generator["Collection", None, None]:
    page = 0
    collections = [None]
    while collections:
        params = {"page": page}
        if limit:
            params["limit"] = limit
        collections = [
            Collection(name)
            for name in get_clustering(f"?{urllib.parse.urlencode(params)}", api_key)
        ]
        yield from collections
        page += 1


@dataclass
class Item:
    id: int
    text: str
    created_at: datetime
    distance: float
    phrase: "Phrase" = field(repr=False)
    cluster: "Cluster" = field(repr=False)

    @classmethod
    def from_dict(cls, phrase: "Phrase", object: dict) -> "Item":
        return cls(
            id=object["id"],
            text=object["original_text"],
            created_at=datetime.strptime(
                object["create_date"], f"%Y-%m-%d %H:%M:%S.%f"
            ),
            distance=object["distance_to_phrase"],
            phrase=phrase,
            cluster=phrase.cluster,
        )


@dataclass
class Phrase:
    id: int
    text: str
    item_count: int
    cluster: "Cluster" = field(repr=False)
    collection: "Collection" = field(repr=False)

    def get_items(self, item_metadata: str = None) -> List[Item]:
        params = {
            "item-metadata": item_metadata,
        }
        url = f"{self.collection.name}/phrases/{self.id}/items" + (
            f"?{urllib.parse.urlencode(params)}" if item_metadata else ""
        )
        return [
            Item.from_dict(self, item)
            for item in get_clustering(url, self.collection.api_key)
        ]

    @classmethod
    def from_dict(cls, cluster: "Cluster", object: dict) -> "Phrase":
        return cls(
            id=object["phrase_id"],
            text=object["text"],
            item_count=object["items_count"],
            cluster=cluster,
            collection=cluster.collection,
        )


@dataclass
class Cluster:
    id: int
    text: str
    phrase_count: int
    metadata: str
    collection: "Collection" = field(repr=False)
    _phrases: List[Phrase] = field(default_factory=list, repr=False)

    def get_phrases(self, item_metadata: str = None) -> List[Phrase]:
        # refetch? cache?
        if self._phrases:
            return self._phrases

        params = {
            "item-metadata": item_metadata,
        }
        url = f"{self.collection.name}/clusters/{self.id}/items" + (
            f"?{urllib.parse.urlencode(params)}" if item_metadata else ""
        )

        return [
            Phrase.from_dict(self, phrase)
            for phrase in get_clustering(url, self.collection.api_key)
        ]

    def add_items(self, items: List[Union[str, Input]]):
        url = f"{self.collection.name}/items"
        data = [
            {
                "text": item.raw if isinstance(item, Input) else item,
                "metadata": item.metadata if isinstance(item, Input) else None,
                "force-cluster-id": self.id,
            }
            for item in items
        ]
        post_clustering(url, data, self.collection.api_key)

    @classmethod
    def from_dict(cls, collection: "Collection", object: dict) -> "Cluster":
        cluster = cls(
            id=object["cluster_id"],
            text=object["cluster_phrase"],
            phrase_count=object["phrases_count"],
            metadata=object["metadata"],
            collection=collection,
        )
        cluster._phrases = [
            Phrase.from_dict(cluster, phrase) for phrase in object["phrases"]
        ]
        return cluster


class Collection:
    api_date_format = "%Y-%m-%d"

    def __init__(self, name: str, api_key: str = None):
        self.name = name
        self.api_key = api_key or oneai.api_key

    def get_clusters(
        self,
        *,
        sort: Literal["ASC", "DESC"] = "ASC",
        limit: int = None,
        from_date: Union[datetime, str] = None,
        to_date: Union[datetime, str] = None,
        date_format: str = api_date_format,
        include_phrases: bool = True,
        phrase_limit: int = None,
        item_metadata: str = None,
    ) -> Generator[Cluster, None, None]:
        if from_date:
            if isinstance(from_date, str):
                from_date = datetime.strptime(from_date, date_format)
            from_date = from_date.strftime(self.api_date_format)

        if to_date:
            if isinstance(to_date, str):
                to_date = datetime.strptime(to_date, date_format)
            to_date = to_date.strftime(self.api_date_format)

        page = 0
        clusters = [None]

        while clusters:
            params = {
                "sort": sort,
                "limit": limit,
                "from-date": from_date,
                "to-date": to_date,
                "include-phrases": include_phrases,
                "phrases-limit": phrase_limit,
                "item-metadata": item_metadata,
                "page": page,
            }
            url = f"{self.name}/clusters?{urllib.parse.urlencode({k: v for k, v in params.items() if v})}"

            clusters = [
                Cluster.from_dict(self, cluster)
                for cluster in get_clustering(url, self.api_key)
            ]
            yield from clusters
            page += 1

    def find(self, query: Union[str, Input], threshold: float = 0.5) -> List[Cluster]:
        params = {
            "text": query.raw if isinstance(query, Input) else query,
            "similarity-threshold": threshold,
        }

        url = f"{self.name}/clusters/find?{urllib.parse.urlencode(params)}"
        return [
            Cluster.from_dict(self, cluster)
            for cluster in get_clustering(url, self.api_key)
        ]

    def add_items(
        self, items: List[Union[str, Input]], force_new_cluster: bool = False
    ):
        url = f"{self.name}/items"
        data = [
            {
                "text": item.raw if isinstance(item, Input) else item,
                "metadata": json.dumps(item.metadata)
                if isinstance(item, Input)
                else None,
                "force-new-cluster": force_new_cluster,
            }
            for item in items
        ]
        print(post_clustering(url, data, self.api_key))

    def __repr__(self) -> str:
        return f"oneai.Collection({self.name})"
