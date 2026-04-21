@echo off
cd /d %~dp0

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate

@REM pip install -r requirements.txt

echo Starting bot...
python -m apps.bot.main