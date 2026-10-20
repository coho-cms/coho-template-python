"""Holds for any project's types, so it keeps passing after you regenerate for yours."""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import httpx
from catalog import Counted, count
from coho_delivery_sdk import ContentConfig, ReleasedConfig

from yourorg_content import content_types


def test_the_catalog_counts_every_type_a_hundred_entries_a_request() -> None:
    # Sizes either side of a page, so some types take more than one request.
    types = sorted(content_types)
    pattern = [30, 100, 170, 0]
    sizes = {slug: pattern[i % 4] for i, slug in enumerate(types)}
    asked: list[str] = []

    def answer(request: httpx.Request) -> httpx.Response:
        query = {
            name: values[0] for name, values in parse_qs(urlparse(str(request.url)).query).items()
        }
        slug, offset, limit = query["type"], int(query["offset"]), int(query["limit"])
        asked.append(f"{slug}@{offset}")
        size = max(0, min(limit, sizes[slug] - offset))
        ids = [f"{slug}-{i}" for i in range(offset, offset + size)]
        entries = {id: {"id": id, "slug": id, "type": slug, "fields": {}} for id in ids}
        body = {
            "roots": ids,
            "entries": entries,
            "unresolved": {},
            "hasMore": offset + size < sizes[slug],
        }
        return httpx.Response(200, content=json.dumps(body))

    counted = count(
        ContentConfig(ReleasedConfig(url="https://delivery.test", project="p1"), ref="qa"),
        httpx.Client(transport=httpx.MockTransport(answer)),
    )

    assert counted == [Counted(slug, sizes[slug]) for slug in types]

    # One request per hundred entries, and one for an empty type: 170 asks at offsets 0 and 100.
    def pages(size: int) -> int:
        return max(1, (size + 99) // 100)

    assert asked == [f"{slug}@{page * 100}" for slug in types for page in range(pages(sizes[slug]))]
