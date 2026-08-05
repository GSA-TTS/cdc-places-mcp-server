#!/bin/bash
# Build the CDC PLACES MCP server container image and push it to GHCR.
#
# The image is consumed by the Obot MCP gateway as a hosted "containerized"
# MCP server (see the mcp-server-hub-catalog entry). It serves MCP over
# streamable HTTP at :8080/mcp with a health check at :8080/health.
#
# Prerequisites:
#   - docker with buildx (for --platform)
#   - Authenticated to GHCR:
#       echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-username> --password-stdin
#     (token needs write:packages scope; authorize SSO for the GSA-TTS org)
#
# Usage:
#   bash scripts/build-and-push.sh
#
# The gateway EC2 host is x86_64, so we build linux/amd64.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

REGISTRY="ghcr.io"
IMAGE="${REGISTRY}/gsa-tts/cdc-places-mcp-server"

# Version tag sourced from pyproject.toml (single source of truth).
VERSION="$(grep -m1 '^version' pyproject.toml | sed -E 's/version\s*=\s*"([^"]+)"/\1/')"
if [[ -z "$VERSION" ]]; then
  echo "FATAL: could not read version from pyproject.toml" >&2
  exit 1
fi

echo "=== Building + pushing ${IMAGE}:${VERSION} and :latest (linux/amd64) ==="
# Single-shot cross-arch build+push. The gateway EC2 host is x86_64, so we
# always target linux/amd64 even when building from an arm64 (Apple Silicon)
# workstation. buildx handles the emulation and pushes both tags.
docker buildx build \
  --platform linux/amd64 \
  -t "${IMAGE}:${VERSION}" \
  -t "${IMAGE}:latest" \
  --push \
  .

echo ""
echo "Pushed:"
echo "  ${IMAGE}:${VERSION}"
echo "  ${IMAGE}:latest"
echo ""
echo "NOTE: On first push, set the GHCR package visibility to PUBLIC so the"
echo "Obot docker runtime backend (which has no image-pull auth) can pull it:"
echo "  GitHub -> Org packages -> cdc-places-mcp-server -> Package settings"
echo "  -> Change visibility -> Public"
