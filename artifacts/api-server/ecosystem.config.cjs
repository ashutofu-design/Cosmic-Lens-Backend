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
    {
      name: "cosmic-telegram",
      cwd: __dirname,
      script: "./run_lr_telegram_poller.py",
      interpreter: "python3",
      env: {
        TELEGRAM_USE_POLLING: "1",
        TELEGRAM_POLL_FROM_API: "0",
      },
      max_restarts: 20,
      min_uptime: "5s",
      restart_delay: 5000,
      exp_backoff_restart_delay: 2000,
    },
  ],
};
