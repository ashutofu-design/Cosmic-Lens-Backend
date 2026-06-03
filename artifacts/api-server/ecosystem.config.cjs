/**
 * PM2 on VPS — keeps gunicorn alive 24/7 (auto-restart on crash / reboot).
 *
 *   cd artifacts/api-server
 *   pm2 start ecosystem.config.cjs
 *   pm2 save && pm2 startup
 */
module.exports = {
  apps: [
    {
      name: "cosmiclens-api",
      cwd: __dirname,
      script: "./start.sh",
      interpreter: "bash",
      env: {
        PROD: "1",
        PORT: "8080",
      },
      max_restarts: 20,
      min_uptime: "10s",
      restart_delay: 3000,
      exp_backoff_restart_delay: 1000,
    },
  ],
};
