#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  echo "Missing .env. Copy .env.example and fill MAX_BOT_TOKEN and MAX_WEBHOOK_SECRET." >&2
  exit 1
fi

required_vars='MAX_BOT_TOKEN MAX_WEBHOOK_SECRET'
for var_name in $required_vars; do
  value=$(grep -E "^${var_name}=" .env | head -n 1 | cut -d= -f2- || true)
  if [ -z "$value" ]; then
    echo "Required variable $var_name is empty in .env." >&2
    exit 1
  fi
done

docker compose up -d --build
docker compose ps

container_id=$(docker compose ps -q max-transport-bot)
if [ -z "$container_id" ]; then
  echo "Container was not created." >&2
  exit 1
fi

status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id")
if [ "$status" != "healthy" ] && [ "$status" != "running" ]; then
  echo "Unexpected container status: $status" >&2
  docker compose logs --tail=100 max-transport-bot
  exit 1
fi
echo "max-transport-bot is running ($status)."

