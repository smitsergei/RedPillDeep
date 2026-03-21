# Deployment Guide

## Production Server
```
IP: 45.12.109.193
User: root
Password: 7sQD6PurjHWy
OS: Ubuntu 24.04 (noble)
Project path: /root/redpilldeep
```

## Quick Deploy (after code changes)
```bash
python deploy_server.py
```

## What the deploy script does:
1. Connects to server via SSH
2. Uploads changed files via SFTP
3. Rebuilds Docker image
4. Restarts container
5. Shows logs

## Files deployed:
- Dockerfile, docker-compose.yml, requirements.txt
- main.py, tg_bot.py, .env
- agents/, core/, tools/ directories

## Container Management (SSH into server):
```bash
# View logs
docker logs -f redpilldeep_redpill_1

# Restart
cd /root/redpilldeep && docker-compose restart

# Full rebuild
cd /root/redpilldeep && docker-compose down && docker-compose build && docker-compose up -d
```

## Current Status:
- Container: `redpilldeep_redpill_1` - running
- Telegram bot: `@RedPillDeep_bot` - active
