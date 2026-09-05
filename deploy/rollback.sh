#!/usr/bin/env bash
set -euo pipefail

readonly root_dir="/opt/polibot"
readonly compose_file="${root_dir}/docker-compose.paper.yml"
readonly previous_file="${root_dir}/state/previous-image"
readonly previous_sha_file="${root_dir}/state/previous-git-sha"

if [[ ! -s "${previous_file}" ]]; then
  echo "No previous image is recorded; rollback cannot proceed." >&2
  exit 1
fi
if [[ ! -s "${previous_sha_file}" ]]; then
  echo "No previous Git SHA is recorded; rollback cannot prove image identity." >&2
  exit 1
fi

previous_image="$(<"${previous_file}")"
if [[ ! "${previous_image}" =~ ^[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/[a-z0-9._/-]+@sha256:[a-f0-9]{64}$ ]]; then
  echo "Recorded previous image is not a valid immutable ECR digest URI." >&2
  exit 1
fi

export POLIBOT_IMAGE="${previous_image}"
export POLIBOT_GIT_SHA="$(<"${previous_sha_file}")"
if [[ ! "${POLIBOT_GIT_SHA}" =~ ^[a-f0-9]{40}$ ]]; then
  echo "Recorded previous Git SHA is invalid." >&2
  exit 1
fi
docker compose --file "${compose_file}" pull app worker
docker compose --file "${compose_file}" up --detach --no-deps worker app

for _ in $(seq 1 30); do
  if "${root_dir}/bin/healthcheck.sh"; then
    printf '%s\n' "${previous_image}" > "${root_dir}/state/current-image"
    printf '%s\n' "${POLIBOT_GIT_SHA}" > "${root_dir}/state/current-git-sha"
    chmod 0600 "${root_dir}/state/current-image" "${root_dir}/state/current-git-sha"
    echo "Application rollback succeeded. Database schema was not downgraded."
    exit 0
  fi
  sleep 2
done

echo "Rollback image did not become healthy." >&2
exit 1
