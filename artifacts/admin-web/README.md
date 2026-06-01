# Cosmic Lens Admin (local)

Browser dashboard for users, payments, and reports. **Not** included in the Play Store app.

## Run locally

1. On the VPS API `.env`: `ADMIN_NO_AUTH=0` and `ADMIN_SECRET=<same secret>` (see `artifacts/api-server/.env.example`).
2. Copy `artifacts/admin-web/.env.example` → `.env` and set `VITE_API_PROXY_TARGET` + `VITE_ADMIN_SECRET` (same as server).
3. From repo root:

```bash
pnpm install
cd artifacts/admin-web
pnpm dev
```

**Windows Rollup error:** From repo root, delete `node_modules` and run `pnpm install` again. Admin uses WASM Rollup (`@rollup/wasm-node`) so native binaries are not required.

4. Open http://127.0.0.1:5174

Vite proxies `/api` → `http://127.0.0.1:8080`.

## Production VPS

- Server: `ADMIN_NO_AUTH=0`, `ADMIN_SECRET=...` — admin routes require `X-Admin-Token` header.
- Local admin only: keep `.env` secret on your PC; do not commit it.
- Optional static build: `pnpm --filter @workspace/admin-web build` — serve `dist/` on a private URL only.
