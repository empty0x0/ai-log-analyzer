#!/bin/bash
# =============================================================================
# GCP Access Token Refresh Sidecar
# =============================================================================
# Runs as a sidecar container, refreshes GCP access token every 45 minutes
# Writes token to /var/run/secrets/gcp-token for Envoy Lua filter to read
# =============================================================================

set -e

TOKEN_FILE="/var/run/secrets/gcp-token"
REFRESH_INTERVAL=2700  # 45 minutes (token valid for 1 hour)

mkdir -p "$(dirname "$TOKEN_FILE")"

echo "[token-refresh] Starting GCP token refresh loop..."

while true; do
    echo "[token-refresh] Refreshing GCP access token..."

    # Get token using Application Default Credentials
    TOKEN=$(gcloud auth print-access-token 2>/dev/null || echo "")

    if [ -n "$TOKEN" ]; then
        echo "$TOKEN" > "$TOKEN_FILE"
        echo "[token-refresh] Token refreshed successfully at $(date)"
    else
        echo "[token-refresh] ERROR: Failed to get access token"
    fi

    sleep "$REFRESH_INTERVAL"
done
