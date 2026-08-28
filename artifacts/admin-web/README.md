# Cosmic Lens web (public site + admin)

Public marketing homepage is `/`. The existing admin dashboard is preserved at `/admin` and still requires login. Help & Support is `/help-support`.

Browser dashboard for users, payments, and reports. **Not** included in the Play Store app.

## Permanent access (production admin + data)

Your laptop must reach VPS **port 80**. If you see `ETIMEDOUT`, fix **Hostinger Firewall** (not a code bug).

### A) VPS (Browser Terminal) — once

```bash
cd /root/Cosmic-Lens-Backend
bash scripts/vps-permanent-access-fix.sh
```

### B) Hostinger hPanel — permanent firewall

1. [hPanel](https://hpanel.hostinger.com) → **VPS** → your server  
2. **Security** → **Firewall** → **Add rule**  
3. Inbound **Accept**: TCP **22**, **80**, **443**  
4. Save, wait 2 minutes  

### D) If Hostinger firewall already open but laptop still ETIMEDOUT

Run on **VPS**:
```bash
bash scripts/vps-diagnose-network.sh
```

Run on **laptop**:
```powershell
Test-NetConnection 187.127.174.55 -Port 80
Test-NetConnection 187.127.174.55 -Port 443
tracert 187.127.174.55
```

| Result | Cause | Permanent fix |
|--------|-------|----------------|
| VPS public :80 **FAIL** | Hostinger edge / VPS ufw | `ufw allow 80` on VPS + Hostinger support ticket |
| VPS public :80 **OK**, laptop **FAIL** | ISP blocks datacenter IP | **Cloudflare proxy** on `api.cosmiclens.app` + use `https://api.cosmiclens.app` in `.env` |
| Port 443 OK, 80 FAIL | ISP blocks only :80 | Use HTTPS only |

**Cloudflare (permanent when ISP blocks IP):**
1. Domain DNS in Cloudflare
2. A record `api` → `187.127.174.55` — **Proxied (orange cloud)**
3. SSL mode: Full
4. Laptop `.env`: `VITE_API_PROXY_TARGET=https://api.cosmiclens.app`
5. Admin browser: `https://api.cosmiclens.app` or separate `admin` subdomain

```powershell
cd D:\Cosmic-Lens-Backend
.\scripts\windows-permanent-admin-setup.ps1
```

### Permanent URLs (after firewall)

| Use | URL |
|-----|-----|
| Public homepage | `http://187.127.174.55/` |
| Admin panel (login required) | `http://187.127.174.55/admin` |
| Help & Support | `http://187.127.174.55/help-support` |
| pnpm dev UI | `http://127.0.0.1:5174` + `.env` → `VITE_API_PROXY_TARGET=http://187.127.174.55` |
| Mobile / API | `https://api.cosmiclens.app` (DNS A → 187.127.174.55) |

## Temporary tunnel (only if firewall cannot be opened)

```bash
bash scripts/vps-expose-api-tunnel.sh
```

## Production VPS

- Server: `ADMIN_NO_AUTH=0`, `ADMIN_SECRET=...` — admin routes require `X-Admin-Token` header.
- Local admin only: keep `.env` secret on your PC; do not commit it.
- Optional static build: `pnpm --filter @workspace/admin-web build` — serve `dist/` on a private URL only.
