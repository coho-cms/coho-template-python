"""
`uv run tools/catalog.py`: every content type, and how many entries each has, read the way an
app reads them. Run it from the repository's root.

Released content by default, from delivery, with COHO_DELIVERY_URL and COHO_DELIVERY_KEY. The
ref is `--ref`, or COHO_REF, or the ref in coho.config.json.

`--preview` reads unreleased content instead, live through Coho, with the COHO_TOKEN this
library pulls its types with, or COHO_PREVIEW_TOKEN if that is set. The ref is `--ref`, or
`dev`.

The project, and for a preview Coho's URL and the account, come from coho.config.json unless
the environment or `.env` sets them, under the names an app's configuration uses.

A development tool: it is not part of the package, so it is never published.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx
from coho_delivery_sdk import CohoDeliveryError, ContentConfig, DeliveryClient, config_from_env

from yourorg_content import content_types


@dataclass(frozen=True)
class Counted:
    """How many entries one content type has."""

    type: str
    count: int


def count(config: ContentConfig, http_client: httpx.Client | None = None) -> list[Counted]:
    """
    Every content type this library was generated for, with how many entries of its own it
    has on the config's ref.

    Each is counted by paging through its list, a hundred entries a request. A type's list
    holds the types that extend it too, so only entries of the type itself are counted. It
    is for looking around, not for every page view.
    """
    counted: list[Counted] = []
    with DeliveryClient(config.delivery, http_client=http_client, cache_size=0) as delivery:
        for slug in sorted(content_types):
            own = 0
            offset = 0
            while True:
                page = delivery.entries(config.ref, type=slug, limit=100, offset=offset)
                own += sum(1 for id in page["roots"] if page["entries"][id]["type"] == slug)
                offset += len(page["roots"])
                if not page["hasMore"] or not page["roots"]:
                    break
            counted.append(Counted(slug, own))
    return counted


def _dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            name, equals, value = line.partition("=")
            if equals and name.strip() and not line.lstrip().startswith("#"):
                values[name.strip()] = value.strip().strip('"')
    return values


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="tools/catalog.py", description="Count the entries of each content type."
    )
    parser.add_argument(
        "--preview", action="store_true", help="read unreleased content, with COHO_TOKEN"
    )
    parser.add_argument("--ref", help="the tag, environment or branch to read")
    options = parser.parse_args(argv)

    configured = json.loads(Path("coho.config.json").read_text(encoding="utf-8"))
    # The variables an app would set: the environment, then .env, with gaps filled from coho.config.json.
    env: dict[str, str | None] = {**_dotenv(Path(".env")), **os.environ}

    def fill(name: str, value: str | None) -> None:
        if not (env.get(name) or "").strip():
            env[name] = value

    fill("COHO_PROJECT", configured.get("project"))
    if options.preview:
        fill("COHO_PREVIEW_TOKEN", env.get("COHO_TOKEN"))
        if not (env.get("COHO_PREVIEW_TOKEN") or "").strip():
            print(
                "The catalog's --preview needs COHO_TOKEN in .env, a project token with read access. See .env.example.",
                file=sys.stderr,
            )
            return 1
        fill("COHO_URL", configured.get("url"))
        fill("COHO_ACCOUNT", configured.get("account"))
        env["COHO_DELIVERY_KEY"] = None
        # Not the config's ref: that is a tag, and a preview reads branches.
        env["COHO_REF"] = options.ref or "dev"
    else:
        env["COHO_PREVIEW_TOKEN"] = None
        fill("COHO_REF", configured.get("ref"))
        if options.ref:
            env["COHO_REF"] = options.ref

    try:
        config = config_from_env(env)
    except ValueError as error:
        print(f"The catalog: {error}. See .env.example.", file=sys.stderr)
        return 1

    # Display names, from the type model the code was generated from.
    model = json.loads(
        Path(configured.get("typeModel") or "coho-ir.json").read_text(encoding="utf-8")
    )
    try:
        counted = count(config)
    except CohoDeliveryError as error:
        # Coho's own words, such as KEY_REQUIRED or PROJECT_NOT_FOUND, and what to check.
        print(error, file=sys.stderr)
        return 1

    rows = [
        (each.type, model["types"].get(each.type, {}).get("name", ""), str(each.count))
        for each in counted
    ]
    type_width = max((len(row[0]) for row in rows), default=0)
    name_width = max((len(row[1]) for row in rows), default=0)
    total = sum(each.count for each in counted)

    print(f"{'Unreleased content' if options.preview else 'Content'} on {config.ref}:\n")
    for slug, name, number in rows:
        print(f"  {slug.ljust(type_width)}   {name.ljust(name_width)}   {number.rjust(5)}")
    entries = "entry" if total == 1 else "entries"
    types = "type" if len(counted) == 1 else "types"
    print(f"\n  {total} {entries} in {len(counted)} {types}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
