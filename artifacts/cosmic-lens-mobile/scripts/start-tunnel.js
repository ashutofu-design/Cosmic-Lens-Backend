#!/usr/bin/env node
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const TUNNEL_URL_FILE = '/tmp/expo-tunnel-url';

fs.writeFileSync(TUNNEL_URL_FILE, '');

const env = { ...process.env };

const expo = spawn('pnpm', ['exec', 'expo', 'start', '--tunnel', '--port', process.env.PORT || '18987'], {
  env,
  stdio: ['inherit', 'pipe', 'pipe'],
});

function processLine(line) {
  process.stdout.write(line + '\n');
  const match = line.match(/Metro waiting on (exp:\/\/[^\s]+)/);
  if (match) {
    const url = match[1];
    fs.writeFileSync(TUNNEL_URL_FILE, url);
    process.stdout.write('\n');
    process.stdout.write('=================================================\n');
    process.stdout.write('EXPO GO URL: ' + url + '\n');
    process.stdout.write('QR page:     https://' + (process.env.REPLIT_DEV_DOMAIN || 'localhost:8080') + '/qr\n');
    process.stdout.write('=================================================\n');
    process.stdout.write('\n');
  }
}

let buffer = '';
function onData(data) {
  buffer += data.toString();
  const lines = buffer.split('\n');
  buffer = lines.pop();
  lines.forEach(processLine);
}

expo.stdout.on('data', onData);
expo.stderr.on('data', (d) => process.stderr.write(d));
expo.on('exit', (code) => process.exit(code || 0));

process.on('SIGTERM', () => expo.kill('SIGTERM'));
process.on('SIGINT', () => expo.kill('SIGINT'));
