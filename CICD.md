# CI and local run

## Local

`make up` is the command that starts the app. It builds the app image and starts Mailpit, and Playwright is not in that image. `make e2e` does not boot the image either: Playwright starts `e2e/serve.py`, which runs the app on port 8765 with a stand-in SMTP server on 2525 and its inbox on 8026. None of those ports is one that `make up` uses (8080, 1025, and 8025), so `make e2e` can run while the containers are up.

## Pipeline

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pull requests, on pushes to `main`, and on manual dispatch.

These check jobs run in parallel:

- `release-version` runs `make release-version`. On a pull request it sets `RELEASE_BASE` to that pull request's base branch, and the check fails unless the diff adds one changelog heading, or the branch merged another pull request and also shows that heading.
- `lint` runs `make lint`
- `test` runs `make test`
- `build` runs `make build`

`e2e` runs `make e2e` on every pull request. It does not block deploy.

`deploy-production` runs `make deploy-production` on manual dispatch only, after the four check jobs pass. No host is configured, so that target prints an error and exits 1. There is no staging.
