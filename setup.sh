#!/bin/bash

echo "======================================"
echo "Oracle DB Reporting System - Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi
echo "✓ Python found"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"
echo ""

# Create necessary directories
echo "Creating output directories..."
mkdir -p outputs/{qa_daily_results,level10_dm_open,qa_results_12,cancelled_work_orders,qa_monthly_results,pm_released_work_orders}
mkdir -p logs
mkdir -p sql
echo "✓ Directories created"
echo ""

# Check for configuration
if [ ! -f "configuration/config.py" ]; then
    echo "⚠️  Warning: configuration/config.py not found"
    echo "   Please ensure your configuration files are in place"
fi

echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the app: python run_app.py"
echo ""
echo "The application will be available at:"
echo "  http://localhost:5000"
echo ""
