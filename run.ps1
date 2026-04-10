$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

try {
    docker compose up -d --build api

    docker compose run --rm --interactive `
        -e TERM=xterm-256color `
        -e COLORTERM=truecolor `
        ui
}
finally {
    docker compose stop
}
