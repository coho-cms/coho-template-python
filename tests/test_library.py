"""
Checks that hold for any project's types, so they keep passing after you regenerate for yours.
Add tests for your own reads beside them.
"""

from __future__ import annotations

import json
import re

import httpx
from coho_delivery_sdk import ContentConfig, ReleasedConfig

from yourorg_content import Coho, homepage, source


def test_the_library_names_the_type_model_it_was_generated_from() -> None:
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", source.schema_hash)


def test_a_client_asks_nothing_until_it_is_read_from_and_the_home_page_is_one_request() -> None:
    asked: list[str] = []

    def answer(request: httpx.Request) -> httpx.Response:
        asked.append(str(request.url))
        return httpx.Response(
            200, content=json.dumps({"roots": [], "entries": {}, "unresolved": {}})
        )

    coho = Coho(
        ContentConfig(
            ReleasedConfig(url="https://delivery.test", project=source.project), ref="prod"
        ),
        http_client=httpx.Client(transport=httpx.MockTransport(answer)),
    )
    assert asked == []

    assert homepage(coho) is None
    assert asked == [
        f"https://delivery.test/v1/projects/{source.project}/prod/entries-by-slug/home-page?depth=2"
    ]
