# coho-template-python

The starting point for your content library: a Python package, generated from your Coho CMS project's content types, that your sites and services install. Each content type becomes a Pydantic model in its own module, and the library's client returns them.

It is a skeleton. `coho-ir.json` is an empty placeholder type model, and `src/yourorg_content/coho/` is what it generates: no content types, only the untyped reads, so the template type-checks and tests as it stands. Generating yours in step 3 replaces both, with your project's type model and a module per content type.

## Set up

You need [uv](https://docs.astral.sh/uv/).

1. **Create the library** with `coho-codegen`, which names it for you:

   ```bash
   uvx coho-codegen create acme-content
   cd acme-content
   uv sync
   ```

   The package is `acme-content`, imported as `acme_content`. Or create your repository from this template on GitHub, and rename `yourorg-content` and `yourorg_content` everywhere they appear: the folder under `src`, `pyproject.toml`, `coho.config.json`'s `outDir`, and the code.

2. **Point it at your project** with a project token with read access. Coho says which account and project the token is for, so there are no ids to copy, and the token goes in `.env`, which is in `.gitignore`:

   ```bash
   coho token create --role viewer --label "acme-content library"
   uv run coho-codegen init --url https://app.coho.example --ref v1.4.0
   ```

   For CI, set the same token as the `COHO_TOKEN` secret.

3. **Generate your types**, and commit the type model and the generated code:

   ```bash
   uv run coho-codegen pull
   uv run coho-codegen generate
   uv run pytest
   ```

4. **Choose where it is published.** The release workflow builds the wheel and attaches it to a GitHub release. To publish to a package index instead, such as a private one, add a `uv publish` step with its URL and credentials.

## See what's there

The catalog lists every content type and how many entries it has, read live from delivery with a delivery key, the way an app reads it. Add these to `.env`:

```
COHO_DELIVERY_URL=https://delivery.coho.example
COHO_DELIVERY_KEY=<a delivery key for the project>
COHO_REF=qa
```

`COHO_REF` is the tag or environment to read; leave it empty to read the ref in `coho.config.json`. A key made for one environment reads only that one. Then, from the repository's root:

```bash
uv run tools/catalog.py
```

```
Content on qa:

  blogPost     Blog post         2
  tag          Tag               3
  teamMember   Team member       2

  7 entries in 3 types
```

To see what is on `dev` or a branch, before it is released, add `--preview`. It reads live through Coho with the `COHO_TOKEN` you pull with, and needs no delivery key:

```bash
uv run tools/catalog.py --preview
uv run tools/catalog.py --preview --ref feature/spring-campaign
```

Its code is in `tools/catalog.py`, an example of reading content with the generated types. It is a development tool: it is not in the package, so it is never published.

## When the content types change

Cut a tag in Coho, then:

```bash
uv run coho-codegen pull --ref v1.4.0
uv run coho-codegen generate
```

Review and commit the diff. CI's `check` fails whenever the generated code doesn't match the committed type model.

To release, run the **Release** workflow with the Coho tag and the version to publish. It pulls that tag's types, generates, type-checks, tests and builds.

Your own reads go in `src/yourorg_content/reads.py`, built on the generated ones. `coho/` is regenerated and never edited, so a schema change that breaks one of your reads fails this library's type check, not an app.

## Using the library in an app

For a project with a `blogPost` type:

```bash
uv add acme-content
```

```python
import os

from coho_delivery_sdk import config_from_env
from acme_content import BlogPost, Coho, homepage

coho = Coho(config_from_env(os.environ))

home = homepage(coho)
latest = coho.blog_post.list(order="-publishedAt", limit=3, depth=1)
```

```
# Released content, in production: set as the app's environment.
COHO_DELIVERY_URL=https://delivery.coho.example
COHO_DELIVERY_KEY=<a delivery key>
COHO_PROJECT=0192…
COHO_REF=prod
COHO_LOCALE=en-US
```

`AsyncCoho` has the same reads, awaited, for an async app such as one built on FastAPI. Every read returns Pydantic models, so a FastAPI endpoint can return one as it is, or build its own response from it.

### Previews

To show `dev` or a branch before it is released, such as on a developer's machine or a preview deployment, read it with a project token instead of a delivery key. Only the configuration changes:

```
COHO_URL=https://api.coho.example
COHO_ACCOUNT=0191…
COHO_PROJECT=0192…
COHO_PREVIEW_TOKEN=coho_pt_…
COHO_REF=dev
```

The answers are the same shapes, so the app's code doesn't change. Setting a preview token and a delivery key together is refused.

## Three credentials, kept apart

| | Who holds it | For |
|---|---|---|
| `COHO_TOKEN` | This library's CI, and you when you pull | Reading the content types. Never deployed |
| A delivery key | Each app, on the server | Reading released content at runtime |
| A preview token | An app, on the server, wherever it previews | Reading unreleased content. A project token with the viewer role: `coho token create --role viewer` |

The library reads no configuration of its own, so a key or token is only ever where the app runs, which passes it in. Keep them on the server: a preview token reads everything unreleased.

## Development

```bash
uv run pytest
uv run mypy
uv run ruff check .
uv run ruff format --check .
uv run coho-codegen check
```

These are what CI runs. The generated `coho/` is left out of `ruff`, since it is never edited; `mypy` checks it with everything else.

## License

Apache-2.0
