# Oracle DB Reporting System - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

This guide will get your web frontend up and running quickly.

## What You're Getting

A complete web-based reporting system with:
- **Modern Dashboard** - View statistics and recent reports
- **Report Generator** - Create reports on-demand via web UI
- **Report Browser** - Download and preview all generated reports
- **Real-time Monitoring** - Track report generation progress
- **REST API** - Automate report generation programmatically

## Files Included

```
📁 Your Project
├── 📁 app/                          # Flask application
│   ├── __init__.py                  # App factory
│   ├── 📁 routes/                   # URL routes
│   │   ├── main.py                  # Dashboard
│   │   ├── reports.py               # Report browsing
│   │   └── api.py                   # REST API
│   ├── 📁 static/                   # CSS & JavaScript
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── 📁 templates/                # HTML templates
│       ├── base.html
│       ├── index.html
│       └── reports/
├── run_app.py                       # Application runner
├── requirements.txt                 # Python dependencies
├── setup.sh                         # Automated setup script
├── .env.example                     # Environment variables template
├── README.md                        # Full documentation
└── DEPLOYMENT.md                    # Production deployment guide
```

## Installation (2 Methods)

### Method 1: Automated (Recommended)

```bash
# 1. Make setup script executable (if not already)
chmod +x setup.sh

# 2. Run setup
./setup.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Start the application
python run_app.py
```

### Method 2: Manual

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create directories
mkdir -p outputs/{qa_daily_results,level10_dm_open}
mkdir -p logs

# 4. Start application
python run_app.py
```

## Access the Application

Open your browser to:
```
http://localhost:5000
```

## First Steps

1. **View Dashboard** - See statistics and recent reports
2. **Generate Report** - Click "Generate Report" or press `Ctrl+G`
3. **Browse Reports** - Navigate to "Browse Reports" to see all generated files
4. **Download** - Click download icon on any report

## Project Integration

### Copy to Your Project

```bash
# Navigate to your ORCDB project
cd /path/to/your/orcdb

# Copy the app folder and files
# (The files are in the outputs directory where you ran this)

# Your project structure should look like:
orcdb/
├── app/                    # ← New web frontend
├── configuration/          # ← Your existing files
├── sql/                    # ← Your existing files  
├── outputs/                # ← Your existing files
├── run_qa_daily_report.py  # ← Your existing files
├── run_level10_dm_report.py # ← Your existing files
└── run_app.py              # ← New Flask runner
```

### Update Python Path (if needed)

If your imports don't work, add this to `run_app.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

## Adding Your Reports

The frontend is pre-configured for these reports:
- QA Daily Results (`run_qa_daily_report.py`)
- Level 10 DM Open Work Orders (`run_level10_dm_report.py`)

To add more reports, edit `app/routes/api.py`:

```python
reports = [
    {
        'id': 'your_report',
        'name': 'Your Report Name',
        'description': 'Description here',
        'script': 'your_report_script.py',
        'category': 'your_output_directory'
    },
    # ... existing reports
]
```

## Common Tasks

### Start the Server
```bash
python run_app.py
```

### Change Port
Edit `run_app.py`:
```python
app.run(port=8080)  # Change 5000 to 8080
```

### View Logs
```bash
tail -f logs/orcdb.log
```

### Stop the Server
Press `Ctrl+C` in terminal

## Keyboard Shortcuts

- `Ctrl+G` - Open report generation modal
- `ESC` - Close any modal

## API Usage Examples

### Generate Report via API
```bash
curl -X POST http://localhost:5000/api/reports/run \
  -H "Content-Type: application/json" \
  -d '{"report_id": "qa_daily"}'
```

### Check Job Status
```bash
curl http://localhost:5000/api/jobs/qa_daily_1706633428
```

### List All Jobs
```bash
curl http://localhost:5000/api/jobs
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port (see "Change Port" above)
```

### Reports Not Appearing
1. Check that reports are in the correct output directory
2. Verify `configuration/config.py` paths match
3. Check file permissions

### Import Errors
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Can't Generate Reports
1. Verify Oracle database connection
2. Check SQLcl is installed
3. Test running report scripts manually first:
   ```bash
   python run_qa_daily_report.py
   ```

## Next Steps

- **Customize Styling** - Edit `app/static/css/style.css`
- **Add Authentication** - Implement login system
- **Deploy to Production** - Follow `DEPLOYMENT.md`
- **Add More Reports** - Edit `app/routes/api.py`
- **Configure Email Alerts** - Add notification system

## Support

📖 **Full Documentation**: See `README.md`
🚀 **Production Deployment**: See `DEPLOYMENT.md`
📝 **Configuration**: See `.env.example`

## Features Overview

### Dashboard
- Total reports count
- Reports generated today/this week
- Category breakdown
- Recent reports list
- System status

### Report Generator
- Select report type from UI
- Real-time progress tracking
- Automatic notifications
- Background processing

### Report Browser
- Browse by category
- Search and filter
- Preview metadata
- Direct download

### API
- REST endpoints
- JSON responses
- Job tracking
- System status

## Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` in `app/__init__.py`
- [ ] Set up HTTPS/SSL
- [ ] Configure firewall
- [ ] Use Gunicorn instead of Flask dev server
- [ ] Set up Nginx reverse proxy
- [ ] Configure log rotation
- [ ] Set up backups
- [ ] Add authentication if needed
- [ ] Review security settings

See `DEPLOYMENT.md` for detailed production setup.

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
┌──────▼──────────┐
│  Flask App      │
│  (run_app.py)   │
├─────────────────┤
│  Routes:        │
│  - Dashboard    │
│  - Reports      │
│  - API          │
└──────┬──────────┘
       │
┌──────▼──────────┐
│  Report Scripts │
│  - QA Daily     │
│  - Level 10 DM  │
└──────┬──────────┘
       │
┌──────▼──────────┐
│  Oracle DB      │
│  (via SQLcl)    │
└─────────────────┘
```

## License

Copyright © 2026 Oracle DB Reporting System

---

**Ready to start?** Run `./setup.sh` and open http://localhost:5000! 🎉
