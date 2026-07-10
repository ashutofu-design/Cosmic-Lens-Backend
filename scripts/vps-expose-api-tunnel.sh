#!/bin/bash
# Expose VPS API/admin through Cloudflare quick tunnel (works when home WiFi blocks VPS IP).
# Run ON VPS (Hostinger Browser Terminal). Keep this terminal open.
#
# Copy the https://....trycloudflare.com URL into laptop:
#   artifacts/admin-web/.env  ->  VITE_API_PROXY_TARGET=https://....trycloudflare.com
# Then: pnpm dev  ->  http://127.0.0.1:5174

set -euo pipefail

CF="/usr/local/bin/cloudflared"
if [ ! -x "$CF" ]; then
  echo "Installing cloudflared ..."
  curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" -o "$CF"
  chmod +x "$CF"
fi

echo "Starting tunnel -> http://127.0.0.1:80"
echo "Copy the https://....trycloudflare.com URL into laptop .env:"
echo "  VITE_API_PROXY_TARGET=<that-url>"
echo ""
exec "$CF" tunnel --url http://127.0.0.1:80
