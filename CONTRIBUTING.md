# Contributing

## Checks

```bash
make lint
make test
make e2e
make up
```

`make test` and `make e2e` are the suite. `make test` runs the unit tests on Python 3.15.0, and `make e2e` runs Playwright from `e2e/` against its own local server instead of the app image. That server uses ports 8765, 2525, and 8026, so `make e2e` can run next to `make up`. `make lint` runs ruff and a check for CSS that Firefox 41 and Chrome 46 do not support. `make build` compiles the tree and runs basedpyright, and CI runs it alongside the others.

## Hooks

[pre-commit](https://pre-commit.com) runs whitespace, newline, YAML, large-file, and merge-conflict checks. Install once:

```bash
brew install pre-commit
pre-commit install
```

The hook runs no language formatter; ruff runs through `make lint`.

## Release

`VERSION` holds one semantic version, and the newest `CHANGELOG.md` heading is that version with its date. A pull request that is only its own work adds one heading; a branch that has merged another pull request's branch may also show that heading. Each bullet ends with the issue id, and a docs or tooling change is a patch. `RELEASELOG.md` gets the heading only when a user can see the change. There is no `[Unreleased]` heading.

## Commits

Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`. The subject carries the Linear issue id in brackets, for example `test: [42S-22] add the failing suite`.

## ADRs

Add a file under `docs/adr/<topic>/` with the next `NNNN` in that topic, put the date inside the file, and update [docs/adr/README.md](docs/adr/README.md) in the same change.
