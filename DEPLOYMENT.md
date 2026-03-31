# Production Deployment Guide

This guide covers deploying the Oracle DB Reporting System to a production environment.

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.8+
- Nginx (for reverse proxy)
- Systemd (for service management)
- Oracle Database access
- SQLcl installed

## Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx -y

# Create application user
sudo useradd -m -s /bin/bash orcdb
sudo usermod -aG sudo orcdb
```

## Step 2: Application Deployment

```bash
# Switch to application user
sudo su - orcdb

# Clone/copy application to server
cd /home/orcdb
# (Copy your application files here)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p outputs logs sql

# Set permissions
chmod -R 755 /home/orcdb/orcdb
```

## Step 3: Environment Configuration

```bash
# Copy and edit environment file
cp .env.example .env
nano .env

# Update the following:
# - SECRET_KEY (generate a strong random key)
# - Database credentials
# - Adjust timeouts as needed
```

## Step 4: Systemd Service

Create `/etc/systemd/system/orcdb.service`:

```ini
[Unit]
Description=Oracle DB Reporting System
After=network.target

[Service]
Type=notify
User=orcdb
Group=orcdb
WorkingDirectory=/home/orcdb/orcdb
Environment="PATH=/home/orcdb/orcdb/venv/bin"
ExecStart=/home/orcdb/orcdb/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 600 \
    --access-logfile /home/orcdb/orcdb/logs/access.log \
    --error-logfile /home/orcdb/orcdb/logs/error.log \
    'app:create_app()'

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable orcdb
sudo systemctl start orcdb
sudo systemctl status orcdb
```

## Step 5: Nginx Configuration

Create `/etc/nginx/sites-available/orcdb`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change this

    # Increase timeout for long-running reports
    proxy_read_timeout 600s;
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/orcdb/orcdb/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Max upload size
    client_max_body_size 20M;
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/orcdb /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 6: SSL/TLS Setup (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

## Step 7: Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

## Step 8: Log Rotation

Create `/etc/logrotate.d/orcdb`:

```
/home/orcdb/orcdb/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 orcdb orcdb
    sharedscripts
    postrotate
        systemctl reload orcdb > /dev/null 2>&1 || true
    endscript
}
```

## Step 9: Monitoring

### Check Service Status
```bash
sudo systemctl status orcdb
```

### View Logs
```bash
# Application logs
tail -f /home/orcdb/orcdb/logs/orcdb.log

# Gunicorn logs
tail -f /home/orcdb/orcdb/logs/error.log
tail -f /home/orcdb/orcdb/logs/access.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Monitor Resources
```bash
# CPU and memory usage
htop

# Disk usage
df -h
du -sh /home/orcdb/orcdb/outputs/*
```

## Step 10: Backup Strategy

### Daily Backup Script

Create `/home/orcdb/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/orcdb/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/orcdb_backup_$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
tar -czf $BACKUP_FILE \
    -C /home/orcdb/orcdb \
    --exclude='venv' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    .

# Keep only last 30 days
find $BACKUP_DIR -name "orcdb_backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

Add to crontab:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/orcdb/backup.sh >> /home/orcdb/logs/backup.log 2>&1
```

## Maintenance Commands

### Restart Application
```bash
sudo systemctl restart orcdb
```

### Update Application
```bash
sudo su - orcdb
cd /home/orcdb/orcdb
source venv/bin/activate
git pull  # or copy new files
pip install -r requirements.txt
sudo systemctl restart orcdb
```

### Clear Old Reports
```bash
# Remove reports older than 90 days
find /home/orcdb/orcdb/outputs -name "*.xlsx" -mtime +90 -delete
```

## Security Checklist

- [ ] Changed SECRET_KEY in production
- [ ] SSL/TLS enabled (HTTPS)
- [ ] Firewall configured
- [ ] Application runs as non-root user
- [ ] Database credentials secured
- [ ] File permissions set correctly (755 for dirs, 644 for files)
- [ ] Regular backups configured
- [ ] Log rotation enabled
- [ ] Security updates automated

## Performance Tuning

### Gunicorn Workers
Adjust based on server resources:
```
workers = (2 * CPU_cores) + 1
```

### Nginx Connection Limits
Edit `/etc/nginx/nginx.conf`:
```nginx
worker_processes auto;
worker_connections 1024;
```

### Database Connection Pool
If needed, configure connection pooling in your database connector.

## Troubleshooting

### Application Won't Start
```bash
# Check service status
sudo systemctl status orcdb

# Check logs
sudo journalctl -u orcdb -n 50

# Check permissions
ls -la /home/orcdb/orcdb
```

### High CPU Usage
```bash
# Check running processes
top -u orcdb

# Check active reports
ps aux | grep python
```

### Disk Space Issues
```bash
# Check disk usage
df -h

# Find large files
du -sh /home/orcdb/orcdb/outputs/*

# Clean old reports
find /home/orcdb/orcdb/outputs -name "*.xlsx" -mtime +30 -delete
```

## Support

For production issues:
1. Check application logs
2. Check system logs (`journalctl`)
3. Verify database connectivity
4. Check network/firewall settings
