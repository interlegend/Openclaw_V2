# OpenClaw Startup & Persistence Guide 🐾

## 1. Systemd Auto-Start (Recommended)
To ensure OpenClaw starts automatically on boot and restarts if it crashes:

### Create the service file:
`sudo nano /etc/systemd/system/openclaw.service`

### Paste this content:
```ini
[Unit]
Description=OpenClaw Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/.openclaw
ExecStart=/usr/bin/python3 /home/ubuntu/.openclaw/bot.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=openclaw

[Install]
WantedBy=multi-user.target
```

### Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw
```

### Check status and logs:
```bash
sudo systemctl status openclaw
journalctl -u openclaw -f
```

## 2. Manual Run
If you just want to run it in your current terminal:
```bash
cd ~/.openclaw
./run.sh
```

## 3. Logs
Commands and their results are logged to:
`~/openclaw_commands.log`
