$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

docker compose down --rmi local --remove-orphans
