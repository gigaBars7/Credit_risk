#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

cleanup() {
  docker compose stop
}

trap cleanup EXIT INT TERM

docker compose up -d --build api

docker compose run --rm --interactive \
  -e TERM=xterm-256color \
  -e COLORTERM=truecolor \
  ui
