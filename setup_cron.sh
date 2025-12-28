#!/bin/bash
# Setup script for PropShop daily cron job

echo "🔧 PropShop Cron Job Setup"
echo "=========================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
SCRAPER_PATH="$SCRIPT_DIR/daily_scraper.py"
LOG_PATH="$SCRIPT_DIR/logs/scraper.log"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Create the cron command (midnight PST = 8 AM UTC)
CRON_CMD="0 8 * * * cd $SCRIPT_DIR && $PYTHON_PATH $SCRAPER_PATH >> $LOG_PATH 2>&1"

echo "This will add the following cron job:"
echo "$CRON_CMD"
echo ""
echo "This runs the scraper every day at midnight PST (8 AM UTC)"
echo ""
read -p "Do you want to proceed? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    
    echo "✅ Cron job added successfully!"
    echo ""
    echo "To verify, run: crontab -l"
    echo "To remove, run: crontab -e (and delete the line)"
    echo ""
    echo "Logs will be saved to: $LOG_PATH"
    echo ""
    echo "💡 To test manually, run:"
    echo "   $PYTHON_PATH $SCRAPER_PATH"
else
    echo "❌ Setup cancelled"
    exit 1
fi
