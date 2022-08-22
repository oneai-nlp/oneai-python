from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import Generator, List, Union
import oneai
from oneai.api import get_clustering, post_clustering
from oneai.classes import Input


def fetch_collections(api_key: str = None):
    return [Collection(name) for name in get_clustering("", api_key)]


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

    @property
    def items(self) -> List[Item]:
        url = f"{self.collection.name}/phrases/{self.id}/items"
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

    @property
    def phrases(self) -> List[Phrase]:
        # refetch? cache?
        return self._phrases

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
    def __init__(self, name: str, api_key: str = None):
        self.name = name
        self.api_key = api_key or oneai.api_key

    @property
    def clusters(self) -> Generator[Cluster, None, None]:
        url = f"{self.name}/clusters"

        page = 0
        clusters = [None]
        while clusters:
            clusters = [
                Cluster.from_dict(self, cluster)
                for cluster in get_clustering(url, self.api_key, page)
            ]
            yield from clusters
            page += 1

    def find(self, query: Union[str, Input], threshold: float=0.5) -> List[Cluster]:
        url = f"{self.name}/clusters/find?text={query.raw if isinstance(query, Input) else query}&similarity-threshold={threshold}"
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
