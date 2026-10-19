#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "$0")" && pwd)"
# Use the scheduler's local timezone. 08:00 UTC is not always midnight Pacific.
PYTHON_BIN="$TASK_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo 'Create .venv and install requirements.txt first.' >&2
  exit 1
fi
if [[ "$TASK_ROOT" == *"'"* || "$TASK_ROOT" == *'%'* ]]; then
  echo 'Cron setup does not support paths containing quotes or percent signs.' >&2
  exit 1
fi
mkdir -p "$TASK_ROOT/logs"
TASK_CRON="0 0 * * * cd '$TASK_ROOT' && '$PYTHON_BIN' daily_scraper.py >> '$TASK_ROOT/logs/scraper.log' 2>&1 # propshop-daily"
echo 'Live collection requires restored source access. A daily snapshot expires after 15 minutes.'
echo 'This optional job runs at midnight in the cron daemon timezone, without a visible browser.'
printf '%s\n' "$TASK_CRON"
read -r -p 'Install this optional cron job? [y/N] ' response
if [[ "$response" == 'y' || "$response" == 'Y' ]]; then
  if crontab -l 2>/dev/null | grep -Fq '# propshop-daily'; then
    echo 'A PropShop cron job already exists. Inspect crontab -e to change it.'
    exit 0
  fi
  { crontab -l 2>/dev/null || true; printf '%s\n' "$TASK_CRON"; } | crontab -
  echo 'Installed. Inspect with crontab -l.'
fi
