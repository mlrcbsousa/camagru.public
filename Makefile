# Targets follow the usual 42 set: all, clean, fclean, re, and .PHONY.
# https://github.com/42School/norminette
# clean stops this project. fclean also deletes its database volume.
# It does not prune every container on the machine.

DOCKER ?= docker

.PHONY: all up down logs db clean fclean re release-version lint test build e2e e2e-stop deploy-production

# https://docs.docker.com/compose/intro/compose-application-model/
# --build rebuilds the image. Without it, compose keeps the previous image
# and the browser keeps showing the old pages.
# -d gives the terminal back. Follow output with `make logs`.
all: up

up:
	$(DOCKER) compose up --build -d

down:
	$(DOCKER) compose down

logs:
	$(DOCKER) compose logs -f --tail=200

# docker compose exec runs Python inside the app container.
# The file is /data/camagru.sqlite3 on the named volume. Rebuilding the image
# does not delete that volume, which is why users survive `make up`.
# `make fclean` deletes the volume. The printed value is the hash, not the password.
# https://docs.docker.com/reference/cli/docker/compose/exec/
db:
	@$(DOCKER) compose exec app python -c 'import os,sqlite3; c=sqlite3.connect(os.environ["DATABASE_PATH"]); c.row_factory=sqlite3.Row; \
[print(r["username"], "|", r["password"]) for r in c.execute("select username, password from users")]'

clean: down

fclean:
	$(DOCKER) compose down -v --rmi local

re: down up

# https://keepachangelog.com/en/1.1.0/
release-version:
	sh scripts/check-release.sh

# https://docs.astral.sh/ruff/
# The second line fails on CSS that Firefox 41 and Chrome 46 do not support.
# https://caniuse.com/css-grid https://caniuse.com/flexbox-gap https://caniuse.com/mdn-css_properties_aspect-ratio
lint:
	uvx ruff check .
	@! grep -nE '^[[:space:]]*(display:[[:space:]]*grid|(row-|column-)?gap:|aspect-ratio:|inset:)' public/*.css || { echo "CSS newer than Firefox 41 / Chrome 46" >&2; exit 1; }

# https://docs.astral.sh/uv/
# https://docs.python.org/3.15/library/unittest.html
test:
	PYTHONPATH=. uv run --python 3.15.0 python -m unittest discover -s tests

# https://docs.python.org/3.15/library/compileall.html
# https://docs.basedpyright.com/latest/
build:
	uv run --python 3.15.0 python -m compileall -q .
	uv run --python 3.15.0 --with basedpyright basedpyright

# https://playwright.dev/docs/intro
e2e:
	cd e2e && npm ci && npx playwright install --with-deps chromium && npm run e2e

e2e-stop:
	-pkill -f e2e/serve.py || true

deploy-production:
	@echo "production deploy is not configured" >&2
	@exit 1
