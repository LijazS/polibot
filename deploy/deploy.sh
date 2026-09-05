#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: deploy.sh <immutable-image-uri> <git-sha> <aws-region>" >&2
  exit 2
fi

readonly new_image="$1"
readonly git_sha="$2"
readonly aws_region="$3"
readonly root_dir="/opt/polibot"
readonly secrets_dir="${root_dir}/secrets"
readonly state_dir="${root_dir}/state"
readonly script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly compose_file="${root_dir}/docker-compose.paper.yml"

if [[ ! "${new_image}" =~ ^[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/[a-z0-9._/-]+@sha256:[a-f0-9]{64}$ ]]; then
  echo "Image must be an immutable ECR digest URI." >&2
  exit 2
fi
if [[ ! "${git_sha}" =~ ^[a-f0-9]{40}$ ]]; then
  echo "Git SHA must contain exactly 40 lowercase hexadecimal characters." >&2
  exit 2
fi
if [[ ! "${aws_region}" =~ ^[a-z]{2}(-gov)?-[a-z]+-[0-9]$ ]]; then
  echo "AWS region has an invalid format." >&2
  exit 2
fi

install -d -m 0750 "${root_dir}" "${root_dir}/bin" "${state_dir}"
install -d -m 0700 "${secrets_dir}"
install -m 0640 "${script_dir}/docker-compose.paper.yml" "${compose_file}"
install -m 0750 "${script_dir}/healthcheck.sh" "${root_dir}/bin/healthcheck.sh"
install -m 0750 "${script_dir}/rollback.sh" "${root_dir}/bin/rollback.sh"
install -m 0750 "${script_dir}/deploy.sh" "${root_dir}/bin/deploy.sh"

if [[ ! -s "${secrets_dir}/postgres.env" || ! -s "${secrets_dir}/runtime.env" ]]; then
  umask 077
  database_password="$(openssl rand -hex 32)"
  {
    printf 'POSTGRES_DB=polibot\n'
    printf 'POSTGRES_USER=polibot\n'
    printf 'POSTGRES_PASSWORD=%s\n' "${database_password}"
  } > "${secrets_dir}/postgres.env"
  {
    printf 'POLIBOT_EXECUTION_MODE=paper\n'
    printf 'POLIBOT_LIVE_TRADING_ENABLED=false\n'
    printf 'POLIBOT_DATABASE_URL=postgresql+asyncpg://polibot:%s@postgres:5432/polibot\n' "${database_password}"
    printf 'POLIBOT_LOG_LEVEL=INFO\n'
  } > "${secrets_dir}/runtime.env"
  unset database_password
fi
chmod 0600 "${secrets_dir}/postgres.env" "${secrets_dir}/runtime.env"

if ! grep -qx 'POLIBOT_EXECUTION_MODE=paper' "${secrets_dir}/runtime.env" ||
  ! grep -qx 'POLIBOT_LIVE_TRADING_ENABLED=false' "${secrets_dir}/runtime.env"; then
  echo "Runtime safety configuration is missing or unsafe." >&2
  exit 1
fi

if [[ -s "${state_dir}/current-image" ]]; then
  install -m 0600 "${state_dir}/current-image" "${state_dir}/previous-image"
fi

registry="${new_image%%/*}"
aws ecr get-login-password --region "${aws_region}" |
  docker login --username AWS --password-stdin "${registry}" >/dev/null
export POLIBOT_IMAGE="${new_image}"

docker compose --file "${compose_file}" pull
docker compose --file "${compose_file}" up --detach postgres

postgres_id="$(docker compose --file "${compose_file}" ps --quiet postgres)"
for _ in $(seq 1 30); do
  if [[ "$(docker inspect --format '{{.State.Health.Status}}' "${postgres_id}")" == "healthy" ]]; then
    break
  fi
  sleep 2
done
if [[ "$(docker inspect --format '{{.State.Health.Status}}' "${postgres_id}")" != "healthy" ]]; then
  echo "PostgreSQL did not become healthy." >&2
  exit 1
fi

docker compose --file "${compose_file}" run --rm --no-deps app alembic upgrade head
docker compose --file "${compose_file}" up --detach --no-deps app

deployment_ok=false
for _ in $(seq 1 30); do
  if "${root_dir}/bin/healthcheck.sh"; then
    deployment_ok=true
    break
  fi
  sleep 2
done

if [[ "${deployment_ok}" != "true" ]]; then
  echo "New image failed health/safety verification; attempting application rollback." >&2
  if [[ -s "${state_dir}/previous-image" ]]; then
    "${root_dir}/bin/rollback.sh"
  fi
  exit 1
fi

printf '%s\n' "${new_image}" > "${state_dir}/current-image"
printf '%s\n' "${git_sha}" > "${state_dir}/current-git-sha"
chmod 0600 "${state_dir}/current-image" "${state_dir}/current-git-sha"
docker image prune --force --filter 'until=168h' >/dev/null
echo "PAPER deployment passed health and execution-mode checks for ${git_sha}."

