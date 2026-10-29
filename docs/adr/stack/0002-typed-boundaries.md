# ADR 0002: Typed boundaries

Date: 2026-10-27

## Status

Accepted

## Context

basedpyright's `basic` mode type-checks almost nothing while function arguments are unannotated, and sqlite rows and the WSGI environ are `Any` in the standard-library stubs. A project-wide ban on every `Any` expression, including unused-result warnings, pushes edits that delete side effects. `make up` does not run the type checker; `make build` does, and it stays under a second either way.

## Decision

We will type every function argument and return in `app/` and `tests/`, and the Playwright files in `e2e/` carry JSDoc types that no checker runs. A local is typed when its type is known, whether inferred or written. basedpyright runs in `strict` mode with `reportAny` as an error, and `reportExplicitAny` stays off so a bottleneck may name `Any`.

The only reads of sqlite values and the WSGI environ are in `app/boundary.py`, where each read is cast to `object` and checked. A column or header of the wrong type raises `TypeError` or `ValueError`, which the request handler already turns into the short 500 page. Posted fields are a `TypedDict`: missing or non-text values become `""`, and `frames` stays a list of text. A Pillow call whose stub is still unknown may carry one `# pyright: ignore[reportUnknownMemberType]`.

## Consequences

`make build` fails when a new function has no argument or return type, or when an `Any` value leaves `app/boundary.py`. Corrupt database rows and a non-numeric `Content-Length` fail the request instead of being treated as a user. Inferred locals are enough, so `i = 0` needs no annotation. HTML, CSS, and browser JavaScript stay untyped. This supersedes the basedpyright sentence in [0001](0001-python-and-sqlite3.md).
